from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from django.db.models import Count, Avg, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from decimal import Decimal
from functools import reduce
import requests
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Min, Max
from django.db.models import Min, Max, Case, When, Value, BooleanField
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import  CommentSerializer
from .models import Product, Comment
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination

from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Category
from .serializers import CategoriesSerializer
import logging
from rest_framework.views import APIView
from .models import Product, Category, Comment, BodyType
from .serializers import ProductSerializerHomepage, CategoriesSerializer,  FavoriteProductListSerializer  , CommentSerializer, ProductSerializerll, ProductDetailSerializer
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from django.db.models import Q
from itertools import combinations
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
from .filters import ProductFilterall
from django_filters.rest_framework import DjangoFilterBackend
logger = logging.getLogger(__name__)

import logging
logger = logging.getLogger(__name__)



class ProductAutocompleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    manufacturer = serializers.CharField()
    model = serializers.CharField()

class ProductAutocompleteView(APIView):
    """
    Эндпоинт для живого поиска (автодополнение).
    """
    @swagger_auto_schema(
        tags=['Product'],
        operation_summary="Автодополнение для товаров",
        operation_description="Этот эндпоинт предоставляет автодополнение для товаров, включая их название, производителя и модель.",
        manual_parameters=[
            openapi.Parameter(
                'q',  # имя параметра
                openapi.IN_QUERY,  # где будет использоваться параметр (в запросе)
                description='Текст для поиска товаров. Может быть частью названия товара, производителя или модели.',
                required=True,  # параметр обязательный
                type=openapi.TYPE_STRING,  # тип параметра
                example='giog'  # пример значения параметра
            )
        ],
        responses={
            200: openapi.Response(
                description='Успешный ответ с результатами автодополнения.',
                schema=ProductAutocompleteSerializer(many=True)
            ),
            400: openapi.Response(
                description='Ошибка запроса, например, отсутствует параметр "q".'
            ),
            404: openapi.Response(
                description='Товары не найдены, соответствующие запросу.'
            )
        }
    )
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if query:
            products = Product.objects.filter(
                Q(title__icontains=query) |
                Q(manufacturer__icontains=query) |
                Q(model__icontains=query)
            ).only('id', 'title', 'manufacturer', 'model')

            # Сортировка: сначала по title, потом по manufacturer, потом по model
            products = sorted(
                products,
                key=lambda p: (
                    (query.lower() in p.title.lower(), 2),
                    (query.lower() in p.manufacturer.lower(), 1),
                    (query.lower() in p.model.lower(), 0)
                ),
                reverse=True
            )

            return Response([{
                "id": p.id,
                "title": p.title,
                "manufacturer": p.manufacturer,
                "model": p.model
            } for p in products[:10]])

        return Response([])

class HomepageView(ListAPIView):
    """
    **Описание эндпоинта:**

    Этот эндпоинт предоставляет информацию для главной страницы, включая:

    - **Популярные товары**: товары с наибольшим количеством комментариев и самым высоким средним рейтингом.
    - **Товары с акциями**: товары, для которых активны акции, с учетом времени окончания.

    Доступные параметры фильтрации:

    - **manufacturer**: Фильтр по производителю (поиск без учета регистра).
    - **model**: Фильтр по модели (поиск без учета регистра).
    - **generation**: Фильтр по поколению (поиск без учета регистра).
    - **modification**: Фильтр по модификации (поиск без учета регистра).
    - **body_type**: Фильтр по типу кузова (например, "sedan").


    **Ответ:**

    В ответе содержатся следующие разделы:

    - **popularProducts**: Список популярных товаров.
    - **promotions**: Список товаров с активными акциями.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializerHomepage
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'manufacturer', 'model']


    @swagger_auto_schema(
        tags=['Homepage'],
        operation_summary="Получение данных для главной страницы",
        operation_description="Этот эндпоинт возвращает данные для главной страницы, включая популярные товары и товары с акциями.",
        manual_parameters=[
            openapi.Parameter(
                'manufacturer', openapi.IN_QUERY, description="Фильтр по производителю (поиск без учета регистра)",
                type=openapi.TYPE_STRING),
            openapi.Parameter(
                'model', openapi.IN_QUERY, description="Фильтр по модели (поиск без учета регистра)",
                type=openapi.TYPE_STRING),
            openapi.Parameter(
                'generation', openapi.IN_QUERY, description="Фильтр по поколению (поиск без учета регистра)",
                type=openapi.TYPE_STRING),
            openapi.Parameter(
                'modification', openapi.IN_QUERY, description="Фильтр по модификации (поиск без учета регистра)",
                type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Данные для главной страницы",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "popular": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "product_Id": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                                 description="Идентификатор товара"),
                                    "image": openapi.Schema(type=openapi.TYPE_STRING, format="url",
                                                            description="Ссылка на изображение товара"),
                                    "season": openapi.Schema(type=openapi.TYPE_STRING,
                                                                  description="Сезонность товара (например, зимний)"),
                                    "average_rating": openapi.Schema(type=openapi.TYPE_STRING,
                                                                     description="Средний рейтинг товара"),
                                    "comments_count": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                                     description="Количество комментариев к товару"),
                                    "title": openapi.Schema(type=openapi.TYPE_STRING, description="Название товара"),
                                    "in_stock": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                               description="Количество товара в наличии"),
                                    "price": openapi.Schema(type=openapi.TYPE_STRING, description="Цена товара"),
                                    "is_favorite": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                                  description="Признак избранного товара"),
                                }
                            )
                        ),
                        "promotion": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "promotion_id": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                                   description="Идентификатор акции"),
                                    "promotion_image": openapi.Schema(type=openapi.TYPE_STRING, format="url",
                                                                      description="Ссылка на изображение акции"),
                                    "promotion_title": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      description="Название акции"),
                                    "promotion_price": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      description="Цена товара с акцией"),
                                    "promotion_end_time": openapi.Schema(type=openapi.TYPE_STRING,
                                                                         description="Время окончания акции"),
                                    "promotion_category": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Items(type=openapi.TYPE_STRING),
                                        description="Категории товаров с акциями"
                                    ),
                                }
                            )
                        ),
                    }
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Популярные товары
        popular_products = queryset.annotate(
            comments_count=Count('comment'),
            average_rating=Avg('comment__rating')
        ).filter(
            comments_count__gt=0,
            average_rating__isnull=False
        ).order_by(
            F('average_rating').desc(nulls_last=True),
            '-comments_count'
        )

        popular_products_data = [
            {
                "product_Id": product.id,
                "image": product.image.url,
                "season": product.season.label if product.season else None,
                 "average_rating": round(product.average_rating * 2) / 2,
                "comments_count": product.comments_count,
                "title": product.title,
                "in_stock": product.in_stock,
                "price": str(product.price),
                "is_favorite": product.is_favorite,
            }
            for product in popular_products[:4]
        ]

        # Товары с акциями
        promotions = queryset.filter(
            promotion__isnull=False,
            promotion_end_date__gt=timezone.now()
        )

        promotion_data = [
            {
                "promotion_id": product.id,
                "promotion_image": product.image.url,
                "promotion_title": product.title,
                "promotion_price": str(product.promotion),
                "promotion_end_time": self.get_promotion_time_remaining(product.promotion_end_date),
                "promotion_category": product.promotionCategory.split(", ") if product.promotionCategory else [],
            }
            for product in promotions[:3]
        ]
        # Получаем все уникальные ID body_type для продуктов
        ids = Product.objects.values_list('body_type', flat=True).distinct()

        # Получаем значения body_type (например, 'sedan', 'coupe', 'universal') из модели BodyType
        body_type_values = {bt.id: bt.value for bt in BodyType.objects.all()}

        # Преобразуем ID в соответствующие значения
        body_type_values_list = [body_type_values.get(id, 'Unknown') for id in ids]

        # Доступные фильтры
        filters_data = {
            "manufacturers": list(Product.objects.values_list("manufacturer", flat=True).distinct()),
            "models": list(Product.objects.values_list("model", flat=True).distinct()),
            "generations": list(Product.objects.values_list("generation", flat=True).distinct()),
            "modifications": list(Product.objects.values_list("modification", flat=True).distinct()),
            "body_type": body_type_values_list,  # Здесь передаем список значений body_type
        }

        # Создание данных для главной страницы
        homepage_data = {
            "popular": popular_products_data,
            "promotion": promotion_data,
            "filters": filters_data
        }

        return Response(homepage_data)
    @swagger_auto_schema(
        tags=['Homepage'],
        operation_summary="Добавить товар в избранное",
        operation_description="Этот эндпоинт обновляет статус товара в избранном (добавить).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Идентификатор товара"),
                'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                              description="True для добавления в избранное"),
            },
            required=['product_id', 'is_favorite']
        ),
        responses={
            200: openapi.Response(
                description="Обновленный товар",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Идентификатор товара"),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Название товара"),
                        'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                      description="Статус избранного товара"),
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка: отсутствуют обязательные параметры",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Описание ошибки")
                    }
                )
            )
        }
    )
    def post(self, request):
        product_id = request.data.get('product_id')
        is_favorite = request.data.get('is_favorite')

        if not product_id or is_favorite is None:
            return Response({"detail": "Product ID and is_favorite are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем продукт по ID
        product = get_object_or_404(Product, id=product_id)

        # Обновляем поле is_favorite, добавляя в избранное
        product.is_favorite = is_favorite
        product.save()

        # Возвращаем обновленный товар
        return Response({
            "id": product.id,
            "name": product.title,
            "is_favorite": product.is_favorite
        }, status=status.HTTP_200_OK)
    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

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
class CategoriesListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoriesSerializer
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
                    "application/json": {
                        "total_favorites": 3,
                        "favorites": [
                            {
                                "product_Id": 3,
                                "image": "image/upload/v1742982479/lgabfuhfotlzucuvjnpx.jpg",
                                "price": "455.00",
                                "season": 2,
                                "title": "ggg",
                                "in_stock": 50,
                                "is_favorite": True
                            },
                            {
                                "product_Id": 2,
                                "image": "image/upload/v1742982353/hpowq9tsbjla99wgor1j.jpg",
                                "price": "2000.00",
                                "season": 2,
                                "title": "title",
                                "in_stock": 40,
                                "is_favorite": True
                            },
                            {
                                "product_Id": 1,
                                "image": "image/upload/v1742982183/vmh3n2n5wcgunrahzqzh.jpg",
                                "price": "500.00",
                                "season": 3,
                                "title": "turbo",
                                "in_stock": 80,
                                "is_favorite": True
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        # Получаем все избранные продукты
        queryset = Product.objects.filter(is_favorite=True)

        # Сериализуем данные
        serializer = FavoriteProductListSerializer(queryset, many=True)

        # Получаем количество избранных товаров
        total_favorites = queryset.count()

        # Переставляем элементы, чтобы новый товар был в начале
        favorites = serializer.data
        favorites.reverse()  # Меняем порядок на противоположный

        # Возвращаем ответ с добавлением количества товаров в избранном
        return Response({
            "total_favorites": total_favorites,
            "favorites": favorites
        }, status=status.HTTP_200_OK)


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
                    description="Флаг избранного (false - убрать из избранного).",
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
        product_id = request.data.get('product_id')
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

        # Если статус is_favorite True, добавляем товар в избранное через запрос
        if product.is_favorite:
            self.add_to_favorites(product.id)

        # Сериализуем обновленный продукт
        serializer = FavoriteProductListSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def add_to_favorites(self, product_id):
        # Здесь отправляем запрос на /product/favorites/ для добавления товара в избранное
        url = "http://127.0.0.1:8000/product/favorites/"
        data = {
            "product_id": product_id,
            "is_favorite": True
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print(f"Товар с ID {product_id} успешно добавлен в избранное.")
        else:
            print(f"Ошибка при добавлении товара с ID {product_id} в избранное.")
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
        product_id = serializer.validated_data['product_id']
        product = Product.objects.get(id=product_id)
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

class CustomPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 12

    def get_paginated_response(self, data):
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number

        page_numbers = self.get_page_numbers(total_pages, current_page)

        return Response({
            'total_pages': total_pages,
            'current_page': current_page,
            'has_next': self.page.has_next(),
            'has_previous': self.page.has_previous(),
            'next_page': self.page.next_page_number() if self.page.has_next() else None,
            'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
            'pages': page_numbers,  # Список номеров страниц для кнопок
            'products': data
        })

    def get_page_numbers(self, total_pages, current_page):
        """Генерирует список страниц в формате [1, 2, 3, 4, 5, ..., 125]"""
        max_buttons = 5  # Количество кнопок (по 2 слева и справа от текущей страницы)
        pages = []

        if total_pages <= max_buttons:
            pages = list(range(1, total_pages + 1))
        else:
            left = max(1, current_page - 2)
            right = min(total_pages, current_page + 2)

            if left > 1:
                pages.append(1)
                if left > 2:
                    pages.append("...")

            pages.extend(range(left, right + 1))

            if right < total_pages:
                if right < total_pages - 1:
                    pages.append("...")
                pages.append(total_pages)

        return pages

class ProductListView(generics.ListAPIView):
    """
    Получение списка всех товаров.
    Этот эндпоинт теперь применяет фильтрацию, сохраненную в /product/filter/.
    """
    serializer_class = ProductSerializerll
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilterall
    search_fields = ['title', 'manufacturer', 'model']
    ordering_fields = ['price']
    ordering = ['id']

    def get_queryset(self):
        """
        Получаем отфильтрованные товары, если они были сохранены в сессии.
        """
        queryset = Product.objects.all()
        product_filters = self.request.session.get('product_filters')
        if product_filters:
            queryset = ProductFilterall(product_filters, queryset=queryset).qs
        return queryset

    @swagger_auto_schema(
        operation_summary="Получение списка всех товаров",
        operation_description="Этот эндпоинт возвращает список товаров, применяя сохраненные фильтры из `/product/filter/`. Поддерживает пагинацию, поиск по названию и сортировку по цене.",
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="Поиск товаров по названию",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="ordering",
                in_=openapi.IN_QUERY,
                description="Поле для сортировки (пример: `price`, `-price`)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                description="Номер страницы (для пагинации)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                name="page_size",
                in_=openapi.IN_QUERY,
                description="Количество элементов на странице (для пагинации)",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ со списком товаров",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "total_pages": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Общее количество страниц"
                        ),
                        "current_page": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Текущая страница"
                        ),
                        "has_next": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Есть ли следующая страница"
                        ),
                        "has_previous": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Есть ли предыдущая страница"
                        ),
                        "next_page": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            nullable=True,
                            description="Номер следующей страницы, если есть"
                        ),
                        "previous_page": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            nullable=True,
                            description="Номер предыдущей страницы, если есть"
                        ),
                        "pages": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_INTEGER),
                            description="Список доступных страниц"
                        ),
                        "total_count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="общая количество товаров"
                        ),
                        "products": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "product_Id": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="ID товара"
                                    ),
                                    "image": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format=openapi.FORMAT_URI,
                                        description="Ссылка на изображение товара"
                                    ),
                                    "average_rating": openapi.Schema(
                                        type=openapi.TYPE_NUMBER,
                                        format=openapi.FORMAT_FLOAT,
                                        description="Средний рейтинг товара"
                                    ),
                                    "comments_count": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="Количество комментариев к товару"
                                    ),
                                    "title": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Название товара"
                                    ),
                                    "in_stock": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="Количество товара в наличии"
                                    ),
                                    "price": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Цена товара в строковом формате"
                                    ),
                                    "is_favorite": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Флаг избранного товара"
                                    ),
                                    "season": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Сезонность товара  winter(зима), summer(лето), all_season(все сезоны)"
                                                    "season"
                                    ),


                                }
                            )
                        )
                    }
                )
            ),
            400: "Ошибка в запросе",
            500: "Внутренняя ошибка сервера"
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Обрабатывает GET-запрос и применяет фильтрацию.
        """
        products = self.get_queryset()
        total_count = products.count()  # Подсчет всех товаров

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["total_count"] = total_count  # Добавляем total_count в ответ с пагинацией
            return response

        serializer = self.get_serializer(products, many=True)
        return Response({
            'total_count': total_count,  # Добавляем общее количество товаров
            'results': serializer.data
        })

    @swagger_auto_schema(
        operation_summary="Добавление или удаление товара из избранного",
        operation_description="Этот эндпоинт позволяет добавить товар в избранное, если он еще не в нем, или удалить его, если он уже в избранном. Для этого нужно передать `product_id` в теле запроса.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id"],
            properties={
                "product_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID товара, который необходимо добавить в избранное или удалить из него"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешное обновление товара",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "product_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID товара"
                        ),
                        "is_favorite": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Флаг, показывающий, находится ли товар в избранном"
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка, если не был передан `product_id` в запросе"
            ),
            404: openapi.Response(
                description="Ошибка, если товар с указанным `product_id` не найден"
            )
        }
    )
    def post(self, request):
        """
        Обрабатывает POST-запрос для добавления/удаления товара из избранного.
        """
        product_id = request.data.get("product_id")  # Получаем ID из тела запроса
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        product.is_favorite = not product.is_favorite  # Переключаем флаг
        product.save()

        return Response(
            {"product_id": product.id, "is_favorite": product.is_favorite},
            status=status.HTTP_200_OK
        )
class ProductFilterView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializerll
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilterall  # Используем кастомный фильтр

    def list(self, request, *args, **kwargs):
        """
        Фильтрация товаров и сохранение их ID в сессии.
        """
        # ✅ Применяем фильтр
        filtered_products = ProductFilterall(request.GET, queryset=self.queryset).qs
        product_ids = list(filtered_products.values_list('id', flat=True))

        # ✅ Сохраняем отфильтрованные товары в сессии
        request.session["filtered_product_ids"] = product_ids
        request.session["product_filters"] = request.GET.dict()
        request.session.modified = True
        product_filters = self.request.session.get("product_filters")


        # ✅ Список доступных фильтров
        filter_data = {
            "seasons": Product.objects.values_list("season__value", flat=True).distinct(),
            "manufacturers": Product.objects.values_list("manufacturer", flat=True).distinct(),
            "tire_types": Product.objects.values_list("tire_type__value", flat=True).distinct(),
            "conditions": Product.objects.values_list("condition__value", flat=True).distinct(),
            "fuel_efficiency": dict(Product.FUEL_EFFICIENCY_CHOICES),
            "wet_grip": dict(Product.WET_GRIP_CHOICES),
            "min_price": Product.objects.aggregate(min_price=Min("price"))["min_price"],
            "max_price": Product.objects.aggregate(max_price=Max("price"))["max_price"],
            "min_load_index": Product.objects.aggregate(min_load=Min("load_index"))["min_load"],
            "max_load_index": Product.objects.aggregate(max_load=Max("load_index"))["max_load"],
            "min_noise_level": Product.objects.aggregate(min_noise=Min("external_noise_level"))["min_noise"],
            "max_noise_level": Product.objects.aggregate(max_noise=Max("external_noise_level"))["max_noise"],
            "widths": Product.objects.values_list("width", flat=True).distinct(),
            "profiles": Product.objects.values_list("profile", flat=True).distinct(),
            "diameters": Product.objects.values_list("diameter", flat=True).distinct(),
            "speed_indexes": Product.objects.values_list("speed_index", flat=True).distinct(),
            "runflat": Product.objects.values_list("runflat", flat=True).distinct(),
            "off_road": Product.objects.values_list("off_road", flat=True).distinct(),
            "promotion": Product.objects.annotate(
                is_promotion_active=Case(
                    When(promotion__gt=0, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ).values_list('is_promotion_active', flat=True).distinct()
        }

        return Response({
            "message": "Фильтрация сохранена",
            "filtered_product_ids": product_ids,  # ✅ Оставил эту часть
            "filter_data": filter_data  # ✅ Оставил эту часть
        }, status=status.HTTP_200_OK)

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        data = serializer.data

        session_price = request.session.get(f"product_{product.id}_price", float(product.price))
        session_in_stock = request.session.get(f"product_{product.id}_in_stock", product.in_stock)
        session_promotion = request.session.get(f"product_{product.id}_promotion", float(product.promotion) if product.promotion else None)
        session_count = request.session.get(f"product_{product.id}_count", 1)

        request.session.modified = True
        if session_count == 1:
            request.session[f"product_{product.id}_price"] = float(product.price)
            request.session[f"product_{product.id}_promotion"] = float(product.promotion) if product.promotion else None
            request.session[f"product_{product.id}_in_stock"] = product.in_stock

        price = session_price if session_price is not None else float(product.price)
        promotion = session_promotion if session_promotion is not None else (float(product.promotion) if product.promotion else None)
        in_stock = session_in_stock if session_in_stock is not None else product.in_stock

        # Фильтрация похожих товаров
        base_filters = [
            Q(manufacturer=product.manufacturer),
            Q(model=product.model),
            Q(season=product.season),
            Q(diameter=product.diameter),
            Q(width=product.width),
            Q(tire_type=product.tire_type),
        ]

        strict_filters = reduce(lambda x, y: x & y, base_filters)
        similar_products = Product.objects.filter(strict_filters).exclude(id=product.id)

        if similar_products.count() < 5:
            price_range = (product.price * Decimal('0.9'), product.price * Decimal('1.1'))
            relaxed_filters = strict_filters | Q(price__range=price_range)
            similar_products = Product.objects.filter(relaxed_filters).exclude(id=product.id)[:5]

        similar_products_serialized = ProductDetailSerializer(similar_products, many=True).data

        similar_products_data = [
            {
                "id": p["id"],
                "title": p["title"],
                "price": p["price"],
                "rating": p.get("average_rating", 0.0),
                "in_stock": p.get("in_stock"),
                "favorite": p["is_favorite"],
                "season": p["season_value"],
                "image_url": p.get("image_url", None),
                "comments_count": p["comments_count"],
            }
            for p in similar_products_serialized
        ]

        return Response({
            "id": product.id,
            "characteristics": {
                "manufacturer": product.manufacturer,
                "model": product.model,
                "season": product.season.value if product.season else None,
                "width": product.width,
                "profile": product.profile,
                "diameter": product.diameter,
                "speed_index": product.speed_index,
                "load_index": product.load_index,
                "load_index_for_double": product.load_index_for_double,
            },
            "title": data.get("title", product.title),
            "favorite": product.is_favorite,
            "image_url": data.get("image_url", None),
            "promotion": promotion,
            "average_rating": data.get("average_rating", 0.0),
            "comments_count": product.comment_set.count(),
            "model_description": data.get("model_description", ""),
            "price": price,
            "in_stock": in_stock,
            "warranty": data.get("warranty") or "",
            "count": session_count,
            "similar_products": similar_products_data,
        })
    def post(self, request, *args, **kwargs):
        """🔄 Переключение избранного"""
        product = self.get_object()
        product.is_favorite = not product.is_favorite  # Инвертируем статус
        product.save()

        return Response(
            {"id": product.id, "favorite": product.is_favorite},
            status=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        product = self.get_object()
        count = request.data.get("count", 1)  # ✅ count по умолчанию 1

        try:
            count = int(count)
            if count <= 0:
                return Response({"error": "Count must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid count value"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Если count == 1, сбрасываем сессию до состояния БД
        if count == 1:
            request.session[f"product_{product.id}_price"] = float(product.price)
            request.session[f"product_{product.id}_promotion"] = float(
                product.promotion) if product.promotion else None
            request.session[f"product_{product.id}_in_stock"] = product.in_stock
        else:
            total_price = float(product.price) * count
            total_promotion = float(product.promotion) * count if product.promotion else None
            new_in_stock = max(0, product.in_stock - count)

            request.session[f"product_{product.id}_price"] = total_price
            request.session[f"product_{product.id}_promotion"] = total_promotion
            request.session[f"product_{product.id}_in_stock"] = new_in_stock

        request.session[f"product_{product.id}_count"] = count  # ✅ Сохраняем count в сессии
        request.session.modified = True

        return Response({
            "id": product.id,
            "price": request.session[f"product_{product.id}_price"],
            "promotion": request.session[f"product_{product.id}_promotion"],
            "in_stock": request.session[f"product_{product.id}_in_stock"],
            "count": count  # ✅ Добавили count в response
        })

@api_view(["PUT"])
def update_characteristics(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    characteristics_data = request.data.get("characteristics", [])

    if not isinstance(characteristics_data, list):
        return Response({"error": "Invalid format, expected a list"}, status=400)

    # 🔹 Обновляем JSONField
    product.main_characteristics = characteristics_data
    product.save()

    return Response(
        {"message": "Characteristics updated successfully", "main_characteristics": product.main_characteristics})


class CommentLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 3  # Количество комментариев в одной части
    max_limit = 40  # Максимальный лимит, чтобы не перегружать сервер


class ProductCommentListView(generics.ListAPIView):
    """
    Получение всех комментариев к конкретному продукту.
    """
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    pagination_class = CommentLimitOffsetPagination

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        return Comment.objects.filter(product_id=product_id)
