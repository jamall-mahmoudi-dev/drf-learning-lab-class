from django.core.management import call_command

from catalog.models import Book


def test_seed_is_idempotent(db):
    call_command("seed_books")
    first = Book.objects.count()
    assert first >= 30
    call_command("seed_books")
    assert Book.objects.count() == first
    assert len({b.genre for b in Book.objects.all()}) >= 5
