from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class StandardPagination(PageNumberPagination):
    """روش اصلی: ?page=2&page_size=5"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50  # بیشتر از این به 50 کاهش می‌یابد؛ مقدار نامعتبر -> اندازه پیش‌فرض


class OffsetPagination(LimitOffsetPagination):
    """روش جایگزین: ?limit=5&offset=10"""

    default_limit = 10
    max_limit = 50
