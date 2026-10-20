from .conftest import titles


def test_list_response_shape(client, books):
    r = client.get("/api/books/")
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"count", "next", "previous", "results"}
    assert data["count"] == 12
    assert len(data["results"]) == 10  # اندازه پیش‌فرض صفحه


def test_detail(client, books):
    r = client.get(f"/api/books/{books[0].id}/")
    assert r.status_code == 200
    assert r.json()["title"] == "Fluent Python"


def test_anonymous_cannot_write(client, books):
    r = client.post("/api/books/", {"title": "x"}, format="json")
    assert r.status_code == 403


# ---------- Filtering ----------
def test_filter_genre(client, books):
    r = client.get("/api/books/?genre=programming")
    assert r.json()["count"] == 4
    assert all(b["genre"] == "programming" for b in r.json()["results"])


def test_filter_invalid_genre_is_400(client, books):
    assert client.get("/api/books/?genre=nope").status_code == 400


def test_filter_author_icontains(client, books):
    r = client.get("/api/books/?author=tolkien")
    assert r.json()["count"] == 2


def test_filter_is_available(client, books):
    r = client.get("/api/books/?is_available=false")
    assert sorted(titles(r)) == ["Python for Data Analysis", "The Selfish Gene"]


def test_filter_publication_year(client, books):
    assert client.get("/api/books/?publication_year=2015").json()["count"] == 2


def test_filter_price_range(client, books):
    r = client.get("/api/books/?price_min=10&price_max=15")
    prices = [float(b["price"]) for b in r.json()["results"]]
    assert r.json()["count"] == 5
    assert all(10 <= p <= 15 for p in prices)


def test_unlisted_field_is_not_filterable(client, books):
    # description در فیلترهای مجاز نیست؛ نادیده گرفته می‌شود و همه کتاب‌ها می‌آیند
    assert client.get("/api/books/?description=Cosmos").json()["count"] == 12


# ---------- Search & Ordering ----------
def test_search_title_and_author(client, books):
    assert client.get("/api/books/?search=python").json()["count"] == 3
    assert client.get("/api/books/?search=hawking").json()["count"] == 1


def test_ordering_price_desc(client, books):
    r = client.get("/api/books/?ordering=-price")
    assert titles(r)[0] == "Python for Data Analysis"


def test_ordering_title_asc(client, books):
    assert titles(client.get("/api/books/?ordering=title"))[0] == "1984"


def test_invalid_ordering_is_ignored(client, books):
    r = client.get("/api/books/?ordering=description")
    assert r.status_code == 200
    assert titles(r)[0] == "Fluent Python"  # ترتیب پیش‌فرض (id)


# ---------- Pagination ----------
def test_custom_page_size(client, books):
    r = client.get("/api/books/?page=1&page_size=5")
    assert len(r.json()["results"]) == 5
    assert r.json()["next"] is not None


def test_second_page(client, books):
    r = client.get("/api/books/?page=2")
    assert len(r.json()["results"]) == 2
    assert r.json()["next"] is None
    assert r.json()["previous"] is not None


def test_page_size_above_max_is_capped(client, books):
    # max_page_size=50 و فقط 12 کتاب داریم؛ مهم این است که 400/خطا نمی‌گیریم و سقف 50 اعمال می‌شود
    r = client.get("/api/books/?page_size=1000")
    assert r.status_code == 200
    assert len(r.json()["results"]) == 12


def test_page_size_cap_is_enforced(client, db):
    from catalog.models import Book

    Book.objects.bulk_create(
        [Book(title=f"B{i}", author="A", genre="fiction", publication_year=2000, price=1) for i in range(60)]
    )
    r = client.get("/api/books/?page_size=1000")
    assert len(r.json()["results"]) == 50


def test_invalid_page_size_falls_back_to_default(client, books):
    for bad in ("0", "-3", "abc"):
        r = client.get(f"/api/books/?page_size={bad}")
        assert r.status_code == 200
        assert len(r.json()["results"]) == 10


def test_page_out_of_range_is_404(client, books):
    assert client.get("/api/books/?page=99").status_code == 404


def test_offset_pagination(client, books):
    r = client.get("/api/books-offset/?limit=5&offset=10")
    assert r.status_code == 200
    assert len(r.json()["results"]) == 2
    assert r.json()["count"] == 12


def test_offset_limit_cap(client, db):
    from catalog.models import Book

    Book.objects.bulk_create(
        [Book(title=f"B{i}", author="A", genre="fiction", publication_year=2000, price=1) for i in range(60)]
    )
    assert len(client.get("/api/books-offset/?limit=1000").json()["results"]) == 50


# ---------- ترکیب ----------
def test_filter_plus_pagination(client, books):
    r = client.get("/api/books/?genre=programming&page_size=3")
    assert r.json()["count"] == 4
    assert len(r.json()["results"]) == 3
    r2 = client.get("/api/books/?genre=programming&page_size=3&page=2")
    assert len(r2.json()["results"]) == 1


def test_search_ordering_pagination(client, books):
    base = "/api/books/?genre=programming&search=python&ordering=-price&page_size=2"
    p1 = client.get(base + "&page=1")
    p2 = client.get(base + "&page=2")
    assert p1.json()["count"] == 3
    assert titles(p1) == ["Python for Data Analysis", "Fluent Python"]
    assert titles(p2) == ["Python Crash Course"]
    assert p2.json()["next"] is None
