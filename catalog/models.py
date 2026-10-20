from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    class Genre(models.TextChoices):
        FICTION = "fiction", "Fiction"
        FANTASY = "fantasy", "Fantasy"
        SCIENCE = "science", "Science"
        HISTORY = "history", "History"
        PROGRAMMING = "programming", "Programming"
        BIOGRAPHY = "biography", "Biography"

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=20, choices=Genre.choices, db_index=True)
    publication_year = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["title", "author"], name="unique_book_title_author"),
        ]

    def __str__(self):
        return f"{self.title} — {self.author}"
