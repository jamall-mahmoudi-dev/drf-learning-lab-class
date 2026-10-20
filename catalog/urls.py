from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BookOffsetViewSet,
    BookViewSet,
    ClearBooksCacheView,
)

router = DefaultRouter()

router.register(
    prefix="books-offset",
    viewset=BookOffsetViewSet,
    basename="book-offset",
)

router.register(
    prefix="books",
    viewset=BookViewSet,
    basename="book",
)

urlpatterns = [
    path(
        "admin/clear-books-cache/",
        ClearBooksCacheView.as_view(),
        name="clear-books-cache",
    ),
]

urlpatterns += router.urls
