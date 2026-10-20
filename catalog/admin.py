from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "publication_year", "price", "is_available")
    list_filter = ("genre", "is_available")
    search_fields = ("title", "author")
