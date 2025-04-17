from django.contrib import admin
from django.urls import path, include
from config import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views
# Создаем объект schema_view для Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),  # Разрешаем доступ всем
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('product/', include("product.urls")),
    path('users/', include("users.urls")),

    path('cart/', include("cart.urls")),

    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Аутентификация (с редиректом на Swagger после выхода)
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
# Статические файлы
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



