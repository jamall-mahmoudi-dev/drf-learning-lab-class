from django.conf import settings
from django.core.cache import caches
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .filters import BookFilter, StableOrderingFilter
from .models import Book
from .pagination import OffsetPagination
from .permissions import IsAdminOrReadOnly
from .serializers import BookSerializer


class BookQueryMixin:
    """تنظیمات مشترک Filtering/Search/Ordering برای هر دو endpoint فهرست."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, StableOrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author"]
    ordering_fields = ["title", "price", "publication_year"]
    ordering = ["id"]


class BookViewSet(BookQueryMixin, viewsets.ModelViewSet):
    """
    endpoint اصلی: /api/books/  (Pagination پیش‌فرض: PageNumber)

    نکته مهم: cache_page روی متد list گذاشته شده، نه روی dispatch.
    چون Throttling و Permission قبل از list اجرا می‌شوند، حتی پاسخ‌های Cache Hit هم
    از سهمیه Throttling مصرف می‌کنند.
    """

    permission_classes = [IsAdminOrReadOnly]

    @method_decorator(cache_page(settings.BOOKS_CACHE_TTL, cache=settings.BOOKS_CACHE_ALIAS))
    @method_decorator(vary_on_headers("Accept"))
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # زمان تولید پاسخ؛ در پاسخ کش‌شده همین مقدار قدیمی تکرار می‌شود.
        response["X-Generated-At"] = timezone.now().isoformat()
        return response

    @extend_schema(responses=BookSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="search",
        throttle_classes=[ScopedRateThrottle],
    )
    def search(self, request):
        """جست‌وجو با سهمیه جداگانه."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BookOffsetViewSet(BookQueryMixin, viewsets.ReadOnlyModelViewSet):
    """روش جایگزین Pagination: /api/books-offset/?limit=5&offset=10"""

    pagination_class = OffsetPagination


class ClearBooksCacheView(APIView):
    """پاک‌کردن cache کتاب‌ها؛ فقط کاربر staff."""

    permission_classes = [IsAdminUser]

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        caches[settings.BOOKS_CACHE_ALIAS].clear()
        return Response({"detail": "Books cache cleared."})
