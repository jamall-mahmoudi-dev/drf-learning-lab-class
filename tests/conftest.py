import pytest
from django.contrib.auth import get_user_model
from django.core.cache import caches
from rest_framework.test import APIClient

from catalog.models import Book

BOOKS = [
    ("Fluent Python", "Luciano Ramalho", "programming", 2015, "45.00", True),
    ("Python Crash Course", "Eric Matthes", "programming", 2015, "38.50", True),
    ("Python for Data Analysis", "Wes McKinney", "programming", 2012, "48.00", False),
    ("Clean Code", "Robert C. Martin", "programming", 2008, "39.99", True),
    ("Cosmos", "Carl Sagan", "science", 1980, "18.00", True),
    ("A Brief History of Time", "Stephen Hawking", "science", 1988, "15.50", True),
    ("The Selfish Gene", "Richard Dawkins", "science", 1976, "14.00", False),
    ("1984", "George Orwell", "fiction", 1949, "10.00", True),
    ("Brave New World", "Aldous Huxley", "fiction", 1932, "11.00", True),
    ("The Great Gatsby", "F. Scott Fitzgerald", "fiction", 1925, "9.50", True),
    ("The Hobbit", "J.R.R. Tolkien", "fantasy", 1937, "13.50", True),
    ("The Fellowship of the Ring", "J.R.R. Tolkien", "fantasy", 1954, "15.00", True),
]


@pytest.fixture(autouse=True)
def clean_caches():
    """هر تست با cache خالی شروع می‌شود؛ وضعیت قبلی روی نتیجه اثر ندارد."""
    for alias in ("default", "books"):
        caches[alias].clear()
    yield
    for alias in ("default", "books"):
        caches[alias].clear()


@pytest.fixture
def books(db):
    objs = [
        Book.objects.create(
            title=t, author=a, genre=g, publication_year=y, price=p, is_available=av, description=t
        )
        for t, a, g, y, p, av in BOOKS
    ]
    caches["books"].clear()
    return objs


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def student(db):
    return get_user_model().objects.create_user("student_t", password="test-pass")


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser("admin_t", password="test-pass")


@pytest.fixture
def admin_client(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


def titles(response):
    return [b["title"] for b in response.json()["results"]]
