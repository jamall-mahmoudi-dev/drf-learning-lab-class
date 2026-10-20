import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("author", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                (
                    "genre",
                    models.CharField(
                        choices=[
                            ("fiction", "Fiction"),
                            ("fantasy", "Fantasy"),
                            ("science", "Science"),
                            ("history", "History"),
                            ("programming", "Programming"),
                            ("biography", "Biography"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("publication_year", models.PositiveSmallIntegerField()),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("is_available", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["id"],
                "constraints": [
                    models.UniqueConstraint(fields=("title", "author"), name="unique_book_title_author")
                ],
            },
        ),
    ]
