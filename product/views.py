from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from django.db.models import Count, Avg, F

import logging
from rest_framework.views import APIView
from .models import Product, Category, Comment
from .serializers import ProductSerializerHomepage, CategoriesSerializer,  FavoriteProductListSerializer  , CommentSerializer
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from rest_framework.permissions import AllowAny
from django.db.models import Count, Avg, F
from rest_framework import filters
from django.utils import timezone
from .filters import ProductFilter
from datetime import timedelta
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
logger = logging.getLogger(__name__)
class HomepageView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializerHomepage
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_queryset(queryset)  # Применяем фильтрацию
        return queryset

    @swagger_auto_schema(
        tags=['homepage'],
        operation_description="Этот эндпоинт возвращает данные для главной страницы...",
    )
    def list(self, request, *args, **kwargs):
        # Получаем отфильтрованный queryset
        queryset = self.get_queryset()

        # Популярные товары
        products = queryset.annotate(
            comments_count=Count('comment'),
            average_rating=Avg('comment__rating')
        ).filter(
            comments_count__gt=0,
            average_rating__isnull=False
        ).order_by(
            F('average_rating').desc(nulls_last=True),
            '-comments_count'
        )

        popular_products = [
            {
                "productId": product.id,
                "productImg": product.image.url,
                "productTitle": product.title,
                "average_rating": product.average_rating,
                "comments_count": product.comments_count,
                "price": str(product.price),
                "seasonality": product.seasonality,
                "is_favorite": product.is_favorite,
                "in_stock": product.in_stock,
            }
            for product in products[:4]
        ]

        # Акции
        promotions = queryset.filter(
            promotion__isnull=False,
            promotion_end_date__gt=timezone.now()
        )

        promotion_data = [
            {
                "promotionId": product.id,
                "promotionImg": product.image.url,
                "promotionTitle": product.title,
                "promotionPrice": str(product.promotion),
                "promotionEndTime": self.get_promotion_time_remaining(product.promotion_end_date),
                "promotionCategory": [category.value for category in product.promotion_category.all()],
            }
            for product in promotions
        ]

        # Формируем ответ
        homepage_data = {
            "homepage": {
                "popularProducts": popular_products,
                "promotions": promotion_data
            }
        }
        return Response(homepage_data)

    def get_promotion_time_remaining(self, end_date):
        """Вспомогательный метод для расчёта оставшегося времени акции."""
        if not end_date:
            return "Not set"

        time_remaining = end_date - timezone.now()
        if time_remaining.total_seconds() <= 0:
            return "Акция завершена"

        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60
        seconds = time_remaining.seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Category
from .serializers import CategoriesSerializer
class CategoriesListView(APIView):
    """
    API для получения списка категорий и добавления новой категории.
    """

    @swagger_auto_schema(
        operation_summary="Получение списка категорий",
        operation_description="Возвращает список всех категорий с их переводами.",
        responses={200: CategoriesSerializer(many=True)},
    )
    def get(self, request):
        """
        Возвращает список всех категорий.

        **Пример ответа**:
        ```json
        [
            {
                "id": 1,
                "label": "АВТОМОБИЛЬНЫЕ ШИНЫ",
                "value": "Car tires"
            },
            {
                "id": 2,
                "label": "ГРУЗОВЫЕ МАШИНЫ",
                "value": "Trucks"
            }
        ]
        ```
        """
        categories = Category.objects.all()
        serializer = CategoriesSerializer(categories, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Добавление новой категории",
        operation_description="Добавляет новую категорию. Если значение `value` не передано, оно автоматически переводится.",
        request_body=CategoriesSerializer,
        responses={
            201: openapi.Response(
                description="Категория успешно создана",
                examples={
                    "application/json": {"label": "АВТОМОБИЛЬНЫЕ ШИНЫ", "value": "Car tires"}
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                examples={
                    "application/json": {"label": ["This field may not be blank."]}
                },
            ),
        },
    )
    def post(self, request):
        """
        Добавляет новую категорию.

        **Пример запроса**:
        ```json
        {
            "label": "Автомобильные шины"
        }
        ```

        **Пример успешного ответа**:
        ```json
        {
            "label": "АВТОМОБИЛЬНЫЕ ШИНЫ",
            "value": "Car tires"
        }
        ```

        **Ошибки**:
        - `400 Bad Request`: Если `label` пустой или содержит некорректные данные.
        """
        serializer = CategoriesSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response({'label': category.label, 'value': category.value}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class FavoriteProduct(APIView):
    """
    Получение списка избранных продуктов и обновление статуса "избранного".
    """

    @swagger_auto_schema(
        operation_summary="Получение списка избранных продуктов",
        operation_description="Возвращает список всех продуктов, отмеченных как избранные (`is_favorite=True`).",
        responses={
            200: openapi.Response(
                description="Список избранных продуктов",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Продукт 1",
                            "is_favorite": True
                        },
                        {
                            "id": 2,
                            "name": "Продукт 2",
                            "is_favorite": True
                        }
                    ]
                }
            )
        }
    )
    def get(self, request):
        # Получаем все избранные продукты
        queryset = Product.objects.filter(is_favorite=True)
        serializer = FavoriteProductListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Обновление статуса избранного у продукта",
        operation_description=(
            "Обновляет статус `is_favorite` для указанного продукта. "
            "Если `is_favorite` передано, устанавливает его значение. "
            "Если не передано, меняет текущее значение `is_favorite` на противоположное."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id"],
            properties={
                "product_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    title="Product ID",
                    description="ID продукта, у которого меняется статус избранного.",
                ),
                "is_favorite": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    title="Is Favorite",
                    description="Флаг избранного (true - добавить в избранное, false - убрать).",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Статус избранного обновлен",
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "Продукт 1",
                        "is_favorite": True
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                examples={
                    "application/json": {"detail": "Product ID is required."}
                },
            ),
            404: openapi.Response(
                description="Продукт не найден",
                examples={
                    "application/json": {"detail": "Product not found."}
                },
            ),
        }
    )
    def post(self, request):
        # Получаем данные из POST-запроса
        product_id = request.data.get('product_id')  # исправил product_Id на product_id
        is_favorite = request.data.get('is_favorite')

        if product_id is None:
            return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем продукт по ID
        product = get_object_or_404(Product, id=product_id)

        # Если is_favorite передано в запросе, обновляем статус
        if is_favorite is not None:
            product.is_favorite = is_favorite
        else:
            # Если is_favorite не передано, меняем его на противоположное
            product.is_favorite = not product.is_favorite

        # Сохраняем продукт с обновленным значением is_favorite
        product.save()

        # Сериализуем обновленный продукт
        serializer = FavoriteProductListSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CommentCreateView(generics.CreateAPIView):
    """
    Создание комментария с указанием `product_id`.
    """
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Создание комментария",
        operation_description="Добавляет новый комментарий к продукту, указывая `product_id`, текст комментария и рейтинг.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id", "comment", "rating"],
            properties={
                "product_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    title="Product ID",
                    description="ID продукта, к которому добавляется комментарий.",
                ),
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    title="Comment",
                    description="Текст комментария.",
                    minLength=1,
                ),
                "rating": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    title="Rating",
                    description="Рейтинг продукта (от 1 до 5).",
                    minimum=1,
                    maximum=5,
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Комментарий успешно создан",
                examples={
                    "application/json": {
                        "id": 1,
                        "product_id": 10,
                        "comment": "Отличный товар!",
                        "rating": 5
                    }
                },
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                examples={
                    "application/json": {"product_id": ["Продукт с таким ID не найден."]},
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        product_id = self.request.data.get("product_id")  # Теперь используем `product_id`
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValidationError({"product_id": "Продукт с таким ID не найден."})

        serializer.save(product=product)  # Привязываем комментарий к продукту
class ProductCommentListView(generics.ListAPIView):
    """
    Получение всех комментариев к конкретному продукту.
    """
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        return Comment.objects.filter(product_id=product_id)
