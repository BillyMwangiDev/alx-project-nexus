from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Nexus Movie API",
        default_version='v1',
        description="A production-grade movie recommendation API with social features",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@nexusmovies.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

def _health(request):
    """Health endpoint for load balancers / probes"""
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include('apps.movies_api.urls')),

    # Health check
    path('api/health/', _health, name='health'),
]

# API docs: only expose in DEBUG or when explicitly enabled via SHOW_SWAGGER
if settings.DEBUG or getattr(settings, 'SHOW_SWAGGER', False):
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-root'),
    ]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)