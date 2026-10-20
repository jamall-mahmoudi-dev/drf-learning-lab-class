from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from .models import Book


class BookFilter(filters.FilterSet):
    """فقط فیلدهایی که صریحاً اجازه داده‌ایم قابل فیلتر هستند."""

    author = filters.CharFilter(lookup_expr="icontains")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Book
        fields = ["genre", "author", "is_available", "publication_year"]


class StableOrderingFilter(OrderingFilter):
    """
    به انتهای هر ordering کلید id را اضافه می‌کند.
    بدون آن، رکوردهای هم‌قیمت (یا هم‌عنوان) ممکن است بین صفحه‌ها جابه‌جا شوند.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            return queryset.order_by(*ordering, "id")
        return queryset
