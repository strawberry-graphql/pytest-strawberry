"""Runtime field coverage collection for Strawberry schemas."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from hashlib import sha256
from threading import Lock
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict, cast
from weakref import WeakKeyDictionary

import graphql
from graphql import (
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLUnionType,
    build_ast_schema,
    get_named_type,
    parse,
)
from strawberry.extensions import SchemaExtension
from strawberry.schema.schema import Schema
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.graphql import OperationType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator

CoverageMode = Literal["resolvers", "all"]
Coordinate = tuple[str, str]


@dataclass(frozen=True, order=True)
class FieldDefinition:
    """Runtime GraphQL coordinate and its Python-facing display metadata."""

    graphql_type_name: str
    graphql_field_name: str
    python_type_name: str
    python_field_name: str
    explicit_graphql_field_name: str | None

    @property
    def coordinate(self) -> Coordinate:
        """Return the GraphQL coordinate used during execution."""
        return self.graphql_type_name, self.graphql_field_name

    @property
    def display_type_name(self) -> str:
        """Return the Python type name, including an explicit GraphQL alias."""
        if self.python_type_name == self.graphql_type_name:
            return self.python_type_name
        return f"{self.python_type_name} [{self.graphql_type_name}]"

    @property
    def display_field_name(self) -> str:
        """Return the Python field name, including an explicit GraphQL alias."""
        alias = self.explicit_graphql_field_name
        if alias is None or alias == self.python_field_name:
            return self.python_field_name
        return f"{self.python_field_name} [{alias}]"


UniverseKey = tuple[FieldDefinition, ...]


class _GetExtensions(Protocol):
    def __call__(
        self,
        schema: Schema,
        sync: bool = False,  # noqa: FBT001, FBT002
    ) -> list[SchemaExtension]: ...


class _SerializedField(TypedDict):
    graphql_type_name: str
    graphql_field_name: str
    python_type_name: str
    python_field_name: str
    explicit_graphql_field_name: str | None


class _SerializedUniverse(TypedDict):
    fields: list[_SerializedField]
    hits: list[list[str]]


class CoverageSnapshot(TypedDict):
    """JSON-serializable xdist worker output."""

    universes: list[_SerializedUniverse]
    unsupported_subscription_executed: bool


@dataclass
class _Universe:
    fields: UniverseKey
    hits: set[Coordinate] = field(default_factory=set)
    coordinates: frozenset[Coordinate] = field(init=False)

    def __post_init__(self) -> None:
        """Cache the GraphQL coordinates checked for every resolver call."""
        self.coordinates = frozenset(
            field_definition.coordinate for field_definition in self.fields
        )


@dataclass(frozen=True)
class TypeCoverage:
    """Coverage values for one Python type backing a GraphQL object."""

    name: str
    fields: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def percentage(self) -> float:
        """Return this type's rounded field coverage percentage."""
        return _percentage(
            len(self.fields),
            len(self.fields) - len(self.missing),
            observed_schema=True,
        )


@dataclass(frozen=True)
class SchemaCoverage:
    """Coverage values for one distinct field universe."""

    fingerprint: str
    types: tuple[TypeCoverage, ...]
    field_count: int
    hit_count: int

    @property
    def missing_count(self) -> int:
        """Return the number of uncovered fields."""
        return self.field_count - self.hit_count

    @property
    def percentage(self) -> float:
        """Return this schema's rounded field coverage percentage."""
        return _percentage(self.field_count, self.hit_count, observed_schema=True)


@dataclass(frozen=True)
class CoverageReport:
    """Immutable reporter input."""

    schemas: tuple[SchemaCoverage, ...]
    field_count: int
    hit_count: int

    @property
    def observed_schema(self) -> bool:
        """Return whether at least one schema universe was observed."""
        return bool(self.schemas)

    @property
    def missing_count(self) -> int:
        """Return the combined number of uncovered fields."""
        return self.field_count - self.hit_count

    @property
    def percentage(self) -> float:
        """Return combined coverage using the documented empty-schema rules."""
        return _percentage(
            self.field_count,
            self.hit_count,
            observed_schema=self.observed_schema,
        )


class CoverageController:
    """Own schema instrumentation and aggregate field execution data."""

    def __init__(self, mode: CoverageMode, fail_under: float | None) -> None:
        """Initialize an isolated collector for one pytest process."""
        self.mode = mode
        self.fail_under = fail_under
        self.supports_subscriptions = (
            graphql.version_info.major,
            graphql.version_info.minor,
        ) >= (3, 3)
        self.graphql_version = graphql.__version__
        self.threshold_failed = False
        self.missing_worker_output = False

        self._lock = Lock()
        self._schema_universes: WeakKeyDictionary[Schema, UniverseKey] = (
            WeakKeyDictionary()
        )
        self._universes: dict[UniverseKey, _Universe] = {}
        self._unsupported_subscription_executed = False
        self._original_get_extensions: _GetExtensions | None = None
        self._instrumented_get_extensions: _GetExtensions | None = None

    def install(self) -> None:
        """Add the collector to every standard Strawberry schema execution."""
        if self._original_get_extensions is not None:
            return

        original = cast("_GetExtensions", Schema.get_extensions)
        controller = self

        def instrumented_get_extensions(
            schema: Schema,
            sync: bool = False,  # noqa: FBT001, FBT002
        ) -> list[SchemaExtension]:
            universe = controller._observe_schema(schema)
            extensions = original(schema, sync=sync)
            return [_CoverageExtension(controller, universe), *extensions]

        self._original_get_extensions = original
        self._instrumented_get_extensions = instrumented_get_extensions
        setattr(  # noqa: B010
            Schema, "get_extensions", instrumented_get_extensions
        )

    def uninstall(self) -> None:
        """Restore Strawberry's extension factory."""
        original = self._original_get_extensions
        instrumented = self._instrumented_get_extensions
        if original is not None and Schema.get_extensions is instrumented:
            setattr(Schema, "get_extensions", original)  # noqa: B010
        self._original_get_extensions = None
        self._instrumented_get_extensions = None

    def record(self, universe: UniverseKey, coordinate: Coordinate) -> None:
        """Record one eligible field immediately before its resolver is invoked."""
        with self._lock:
            data = self._universes[universe]
            if coordinate in data.coordinates:
                data.hits.add(coordinate)

    def record_unsupported_subscription(self) -> None:
        """Remember that graphql-core could not instrument a subscription."""
        with self._lock:
            self._unsupported_subscription_executed = True

    def mark_missing_worker_output(self) -> None:
        """Mark an xdist worker whose coverage payload was unavailable."""
        self.missing_worker_output = True

    def snapshot(self) -> CoverageSnapshot:
        """Return JSON-serializable data for an xdist controller."""
        with self._lock:
            universes = [
                _SerializedUniverse(
                    fields=[
                        _SerializedField(
                            graphql_type_name=field_definition.graphql_type_name,
                            graphql_field_name=field_definition.graphql_field_name,
                            python_type_name=field_definition.python_type_name,
                            python_field_name=field_definition.python_field_name,
                            explicit_graphql_field_name=(
                                field_definition.explicit_graphql_field_name
                            ),
                        )
                        for field_definition in key
                    ],
                    hits=[list(coordinate) for coordinate in sorted(data.hits)],
                )
                for key, data in sorted(self._universes.items())
            ]
            return CoverageSnapshot(
                universes=universes,
                unsupported_subscription_executed=(
                    self._unsupported_subscription_executed
                ),
            )

    def merge(self, snapshot: CoverageSnapshot) -> None:
        """Merge one xdist worker snapshot."""
        with self._lock:
            for serialized in snapshot["universes"]:
                fields = tuple(
                    FieldDefinition(**serialized_field)
                    for serialized_field in serialized["fields"]
                )
                universe = self._universes.setdefault(fields, _Universe(fields))
                universe.hits.update(
                    (type_name, field_name)
                    for type_name, field_name in serialized["hits"]
                    if (type_name, field_name) in universe.coordinates
                )
            self._unsupported_subscription_executed |= snapshot[
                "unsupported_subscription_executed"
            ]

    def report(self) -> CoverageReport:
        """Calculate immutable coverage values from the current aggregate."""
        with self._lock:
            universes = tuple(
                (key, frozenset(data.hits))
                for key, data in sorted(self._universes.items())
            )

        schemas: list[SchemaCoverage] = []
        for fields, hits in universes:
            type_fields: dict[str, list[FieldDefinition]] = {}
            for field_definition in fields:
                type_fields.setdefault(field_definition.display_type_name, []).append(
                    field_definition
                )

            type_reports: list[TypeCoverage] = []
            for type_name, field_definitions in sorted(type_fields.items()):
                ordered_fields = sorted(
                    field_definitions,
                    key=lambda item: item.display_field_name,
                )
                type_reports.append(
                    TypeCoverage(
                        name=type_name,
                        fields=tuple(
                            field_definition.display_field_name
                            for field_definition in ordered_fields
                        ),
                        missing=tuple(
                            field_definition.display_field_name
                            for field_definition in ordered_fields
                            if field_definition.coordinate not in hits
                        ),
                    )
                )
            schemas.append(
                SchemaCoverage(
                    fingerprint=_fingerprint(fields),
                    types=tuple(type_reports),
                    field_count=len(fields),
                    hit_count=len(
                        hits.intersection(
                            field_definition.coordinate for field_definition in fields
                        )
                    ),
                )
            )

        return CoverageReport(
            schemas=tuple(schemas),
            field_count=sum(schema.field_count for schema in schemas),
            hit_count=sum(schema.hit_count for schema in schemas),
        )

    def subscription_warning_needed(self) -> bool:
        """Return whether an uninstrumented 3.2 subscription was executed."""
        with self._lock:
            return self._unsupported_subscription_executed

    def _observe_schema(self, schema: Schema) -> UniverseKey:
        with self._lock:
            existing = self._schema_universes.get(schema)
        if existing is not None:
            return existing

        fields = _build_fields(
            schema,
            mode=self.mode,
            include_subscriptions=self.supports_subscriptions,
        )
        with self._lock:
            self._schema_universes[schema] = fields
            self._universes.setdefault(fields, _Universe(fields))
        return fields


class _CoverageExtension(SchemaExtension):
    def __init__(self, controller: CoverageController, universe: UniverseKey) -> None:
        self._controller = controller
        self._universe = universe

    def resolve(
        self,
        _next: Callable[..., object | Awaitable[object]],
        root: object,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: object,
    ) -> object | Awaitable[object]:
        self._controller.record(
            self._universe, (info.parent_type.name, info.field_name)
        )
        return _next(root, info, *args, **kwargs)

    def on_execute(self) -> Iterator[None]:
        if (
            not self._controller.supports_subscriptions
            and self.execution_context.operation_type is OperationType.SUBSCRIPTION
        ):
            self._controller.record_unsupported_subscription()
        yield None


def _build_fields(
    schema: Schema, *, mode: CoverageMode, include_subscriptions: bool
) -> UniverseKey:
    document_schema = build_ast_schema(
        parse(schema.as_str()),
        assume_valid_sdl=True,
    )
    roots = [document_schema.query_type, document_schema.mutation_type]
    if include_subscriptions:
        roots.append(document_schema.subscription_type)

    pending = deque(root for root in roots if root is not None)
    visited: set[str] = set()
    fields: set[FieldDefinition] = set()

    while pending:
        object_type = pending.popleft()
        if object_type.name in visited:
            continue
        visited.add(object_type.name)

        for field_name, graphql_field in object_type.fields.items():
            if not field_name.startswith("__"):
                field_definition = _build_field_definition(
                    schema,
                    object_type.name,
                    field_name,
                    mode,
                )
                if field_definition is not None:
                    fields.add(field_definition)

            named_type = get_named_type(graphql_field.type)
            if isinstance(named_type, GraphQLObjectType):
                pending.append(named_type)
            elif isinstance(named_type, GraphQLInterfaceType):
                pending.extend(document_schema.get_possible_types(named_type))
            elif isinstance(named_type, GraphQLUnionType):
                pending.extend(named_type.types)

    return tuple(sorted(fields))


def _build_field_definition(
    schema: Schema,
    type_name: str,
    field_name: str,
    mode: CoverageMode,
) -> FieldDefinition | None:
    strawberry_field = schema.get_field_for_type(field_name, type_name)
    if mode == "resolvers" and (
        strawberry_field is None or strawberry_field.base_resolver is None
    ):
        return None

    type_definition = schema.get_type_by_name(type_name)
    python_type_name = (
        type_definition.origin.__name__
        if isinstance(type_definition, StrawberryObjectDefinition)
        else type_name
    )
    python_field_name = (
        strawberry_field.python_name if strawberry_field is not None else field_name
    )
    explicit_graphql_field_name = (
        strawberry_field.graphql_name if strawberry_field is not None else None
    )
    return FieldDefinition(
        graphql_type_name=type_name,
        graphql_field_name=field_name,
        python_type_name=python_type_name,
        python_field_name=python_field_name,
        explicit_graphql_field_name=explicit_graphql_field_name,
    )


def _percentage(field_count: int, hit_count: int, *, observed_schema: bool) -> float:
    if field_count == 0:
        return 100.0 if observed_schema else 0.0
    return round(hit_count / field_count * 100, 2)


def _fingerprint(fields: UniverseKey) -> str:
    value = "\0".join(
        ":".join(
            (
                field_definition.graphql_type_name,
                field_definition.graphql_field_name,
                field_definition.python_type_name,
                field_definition.python_field_name,
                field_definition.explicit_graphql_field_name or "",
            )
        )
        for field_definition in fields
    )
    return sha256(value.encode()).hexdigest()[:8]
