import django
import strawberry
import strawberry_django
from django.conf import settings
from django.db import models

if not settings.configured:
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[],
    )
django.setup()


class Fruit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        app_label = "coverage_example"

    def __str__(self) -> str:
        return self.name


@strawberry_django.type(Fruit)
class FruitType:
    name: strawberry.auto
    description: strawberry.auto


@strawberry.type
class Query:
    @strawberry.field
    def fruit(self) -> FruitType:
        return Fruit(name="Strawberry", description="A very good berry")


schema = strawberry.Schema(query=Query)


def test_fruit_name() -> None:
    result = schema.execute_sync("{ fruit { name } }")

    assert result.errors is None
    assert result.data == {"fruit": {"name": "Strawberry"}}
