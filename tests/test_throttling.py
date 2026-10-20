import pytest
from rest_framework.throttling import SimpleRateThrottle


@pytest.fixture
def clock(monkeypatch):
    """ساعت قابل کنترل برای Throttling؛ بدون sleep واقعی."""
    now = [1000.0]
    monkeypatch.setattr(SimpleRateThrottle, "timer", staticmethod(lambda: now[0]))
    return now


@pytest.fixture
def low_rates(monkeypatch):
    rates = SimpleRateThrottle.THROTTLE_RATES
    monkeypatch.setitem(rates, "anon", "3/min")
    monkeypatch.setitem(rates, "user", "5/min")
    monkeypatch.setitem(rates, "book-search", "2/min")


def test_anonymous_is_throttled_with_retry_after(client, books, low_rates, clock):
    for _ in range(3):
        assert client.get("/api/books/").status_code == 200
    r = client.get("/api/books/")
    assert r.status_code == 429
    assert "Retry-After" in r


def test_limit_resets_after_window(client, books, low_rates, clock):
    for _ in range(3):
        client.get("/api/books/")
    assert client.get("/api/books/").status_code == 429
    clock[0] += 61
    assert client.get("/api/books/").status_code == 200


def test_cache_hits_still_count_against_throttle(client, books, low_rates, clock):
    # هر 3 درخواست یکسان‌اند (2 تا Cache Hit) ولی چهارمی باز هم 429 می‌گیرد
    statuses = [client.get("/api/books/?genre=science").status_code for _ in range(4)]
    assert statuses == [200, 200, 200, 429]


def test_authenticated_user_has_higher_limit(client, student, books, low_rates, clock):
    client.force_authenticate(student)
    statuses = [client.get("/api/books/").status_code for _ in range(6)]
    assert statuses == [200] * 5 + [429]


def test_scoped_throttle_on_search(client, books, low_rates, clock):
    statuses = [client.get("/api/books/search/?search=python").status_code for _ in range(3)]
    assert statuses == [200, 200, 429]
    # سهمیه scope جدا از سهمیه anon است
    assert client.get("/api/books/").status_code == 200
