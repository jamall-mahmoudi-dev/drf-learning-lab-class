from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("catalog.urls")),
    # مستندات نباید از سهمیه Throttling کاربر مصرف کنند
    path("api/schema/", SpectacularAPIView.as_view(throttle_classes=[]), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema", throttle_classes=[]),
        name="swagger-ui",
    ),
]
