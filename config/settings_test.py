"""تنظیمات تست: cache محلی (بدون Redis) و نرخ‌های بالا؛ تست‌های Throttling نرخ را خودشان پایین می‌آورند."""
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key")
os.environ.setdefault("POSTGRES_DB", "book_catalog")
os.environ.setdefault("POSTGRES_USER", "book_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test-only-password")

from .settings import *  # noqa: E402,F401,F403

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-default",
    },
    BOOKS_CACHE_ALIAS: {  # noqa: F405
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-books",
    },
}

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"anon": "1000/min", "user": "1000/min", "book-search": "1000/min"},
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
