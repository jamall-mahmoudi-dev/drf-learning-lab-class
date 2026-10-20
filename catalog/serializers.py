from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "description", "genre",
            "publication_year", "price", "is_available", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_publication_year(self, value):
        if not 1000 <= value <= 2100:
            raise serializers.ValidationError("سال انتشار باید بین 1000 و 2100 باشد.")
        return value
