from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import MeView
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness + database check for Docker and the reverse proxy.

    Plain Django view, outside DRF, so it needs no token. Returns 503 when
    the database cannot be reached, which marks the container unhealthy.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)

    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/", include("projects.urls")),
    path("api/", include("tasks.urls")),
    path("api/", include("users.urls")),
    path("api/", include("teams.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("discussions.urls")),
    path("api/", include("assistant.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)