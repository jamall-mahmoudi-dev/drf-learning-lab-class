from django.db import connection
from django.test.utils import CaptureQueriesContext

from catalog.models import Book

from .conftest import titles


def get_with_query_count(client, url):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    return response, len(ctx)


def test_second_request_is_served_from_cache(client, books):
    """اثبات Cache Hit: درخواست اول به DB می‌رود، درخواست دوم صفر query دارد."""
    r1, q1 = get_with_query_count(client, "/api/books/")
    r2, q2 = get_with_query_count(client, "/api/books/")
    assert r1.status_code == r2.status_code == 200
    assert q1 > 0
    assert q2 == 0
    assert r1.json() == r2.json()
    assert r1["X-Generated-At"] == r2["X-Generated-At"]


def test_cache_key_depends_on_query_string(client, books):
    client.get("/api/books/?genre=science")  # کش شد
    fiction = client.get("/api/books/?genre=fiction")
    assert fiction.json()["count"] == 3
    assert all(b["genre"] == "fiction" for b in fiction.json()["results"])


def test_different_query_is_a_cache_miss(client, books):
    get_with_query_count(client, "/api/books/?genre=science")
    _, queries = get_with_query_count(client, "/api/books/?genre=fiction")
    assert queries > 0


def test_stale_data_until_cache_is_cleared(client, admin_client, books):
    """تغییر بدون سیگنال (QuerySet.update) کش را پاک نمی‌کند؛ clear endpoint آن را درست می‌کند."""
    first = client.get("/api/books/?search=cosmos").json()["results"][0]
    Book.objects.filter(pk=first["id"]).update(price="99.00")

    stale = client.get("/api/books/?search=cosmos").json()["results"][0]
    assert stale["price"] == first["price"]  # هنوز از cache

    assert admin_client.post("/api/admin/clear-books-cache/").status_code == 200
    fresh = client.get("/api/books/?search=cosmos").json()["results"][0]
    assert fresh["price"] == "99.00"


def test_create_invalidates_cache(client, admin_client, books):
    assert client.get("/api/books/").json()["count"] == 12
    r = admin_client.post(
        "/api/books/",
        {"title": "New Book", "author": "Someone", "genre": "fiction",
         "publication_year": 2024, "price": "20.00", "is_available": True},
        format="json",
    )
    assert r.status_code == 201
    assert client.get("/api/books/").json()["count"] == 13


def test_update_invalidates_cache(client, admin_client, books):
    client.get("/api/books/?search=cosmos")
    admin_client.patch(f"/api/books/{books[4].id}/", {"price": "77.00"}, format="json")
    assert client.get("/api/books/?search=cosmos").json()["results"][0]["price"] == "77.00"


def test_delete_invalidates_cache(client, admin_client, books):
    assert client.get("/api/books/").json()["count"] == 12
    assert admin_client.delete(f"/api/books/{books[0].id}/").status_code == 204
    assert client.get("/api/books/").json()["count"] == 11
    assert "Fluent Python" not in titles(client.get("/api/books/"))


def test_clear_endpoint_requires_staff(client, student):
    assert client.post("/api/admin/clear-books-cache/").status_code == 403
    client.force_authenticate(student)
    assert client.post("/api/admin/clear-books-cache/").status_code == 403
