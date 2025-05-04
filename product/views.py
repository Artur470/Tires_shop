from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from django.db.models import Count, Avg, F
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import ExpressionWrapper, F, DecimalField
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from decimal import Decimal
from functools import reduce
import requests
from django.urls import reverse
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
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Case, When, F, DecimalField
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import QueryDict
import logging
from rest_framework.views import APIView
from .models import Product,  Comment, BodyType, News, TireType
from .serializers import (ProductSerializerHomepage,
                          FavoriteProductListSerializer,
                          CommentSerializer,
                          ProductSerializerll,
                          ProductDetailSerializer,
                          NewsDetailSerializer,
                          NewsSerializer,
                          ProductCreateSerializer,
TireTypeSerializer,
BodyTypeSerializer,
ProductAutoCompleteSerializer


                          )


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
from rest_framework import viewsets

import logging
logger = logging.getLogger(__name__)

from drf_yasg.utils import swagger_auto_schema

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
                'q',
                openapi.IN_QUERY,
                description='Текст для поиска товаров. Может быть частью названия товара, производителя или модели.',
                required=True,
                type=openapi.TYPE_STRING,
                example='giog'
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

    @swagger_auto_schema(
        tags=['Product'],
        operation_summary="Автодополнение для товаров",
        operation_description="Этот эндпоинт предоставляет автодополнение для товаров по названию, производителю или модели. Пользователь может отправить запрос с параметром 'q' для поиска товаров.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'q': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Текст для поиска товаров. Может быть частью названия товара, производителя или модели.',
                    example='giog'
                ),
            },
            required=['q']
        ),
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
    def post(self, request, *args, **kwargs):
        query = request.data.get('q', '').strip()
        if query:
            request.session['product_filters'] = {'search': query}
            request.session.modified = True
            products = Product.objects.filter(
                Q(title__icontains=query) |
                Q(manufacturer__icontains=query) |
                Q(model__icontains=query)
            ).select_related('season').prefetch_related('comment_set')[:10]

            serializer = ProductAutoCompleteSerializer(products, many=True)
            return Response({"products": serializer.data})

        return Response({"products": []})


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
                                    "price": openapi.Schema(type=openapi.TYPE_STRING, description="Цена товара либо же договорная"),
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
        )[:4]

        # ✅ сериализация популярных товаров через ProductSerializerHomepage
        popular_products_data = ProductSerializerHomepage(
            popular_products,
            many=True,
            context={'request': request}
        ).data

        # Товары с акциями
        promotions = queryset.filter(
            promotion__isnull=False,
            promotion_end_date__gt=timezone.now()
        )[:3]

        promotion_data = [
            {
                "promotion_id": product.id,
                "promotion_image": product.image1.url if product.image1 else None,
                "promotion_title": product.title,
                "promotion_price": str(product.promotion),
                "promotion_end_time": self.get_promotion_time_remaining(product.promotion_end_date),
                "promotion_category": product.promotionCategory.split(", ") if product.promotionCategory else [],
            }
            for product in promotions
        ]

        # Уникальные body_type ID
        ids = Product.objects.values_list('body_type', flat=True).distinct()
        body_type_values = {bt.id: bt.value for bt in BodyType.objects.all()}
        body_type_values_list = [body_type_values.get(id, 'Unknown') for id in ids]

        filters_data = {
            "manufacturers": list(Product.objects.values_list("manufacturer", flat=True).distinct()),
            "models": list(Product.objects.values_list("model", flat=True).distinct()),
            "generations": list(Product.objects.values_list("generation", flat=True).distinct()),
            "modifications": list(Product.objects.values_list("modification", flat=True).distinct()),
            "body_type": body_type_values_list,
        }

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
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        requested_flag = request.data.get("is_favorite")

        if requested_flag is not None:
            if requested_flag:
                product.is_favorite = True
                product.favorite_created_at = timezone.now()  # ✅ Всегда обновляем
            else:
                product.is_favorite = False
                product.favorite_created_at = None
        else:
            # Переключаем
            product.is_favorite = not product.is_favorite
            product.favorite_created_at = timezone.now() if product.is_favorite else None

        product.save()

        queryset = Product.objects.filter(is_favorite=True).order_by('-favorite_created_at')
        serializer = FavoriteProductListSerializer(queryset, many=True)
        total_favorites = queryset.count()

        return Response({
            "total_favorites": total_favorites,
            "favorites": serializer.data
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

class FavoriteProduct(APIView):
    serializers = FavoriteProductListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

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
                                "price": "договор",
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
        queryset = Product.objects.filter(is_favorite=True).order_by('-favorite_created_at')
        serializer = FavoriteProductListSerializer(queryset, many=True)
        total_favorites = queryset.count()

        return Response({
            "total_favorites": total_favorites,
            "favorites": serializer.data
        })


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
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        requested_flag = request.data.get("is_favorite")

        if requested_flag is not None:
            if requested_flag:
                product.is_favorite = True
                product.favorite_created_at = timezone.now()  # ✅ Всегда обновляем
            else:
                product.is_favorite = False
                product.favorite_created_at = None
        else:
            # Переключаем
            product.is_favorite = not product.is_favorite
            product.favorite_created_at = timezone.now() if product.is_favorite else None

        product.save()

        queryset = Product.objects.filter(is_favorite=True).order_by('-favorite_created_at')
        serializer = FavoriteProductListSerializer(queryset, many=True)
        total_favorites = queryset.count()

        return Response({
            "total_favorites": total_favorites,
            "favorites": serializer.data
        }, status=status.HTTP_200_OK)

    def add_to_favorites(self, product_id):
        # Здесь отправляем запрос на /product/favorites/ для добавления товара в избранное
        url = self.request.build_absolute_uri(reverse('favorite-products'))
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
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    """ 
    Создание комментария с указанием `product_id`.
    """
    serializer_class = CommentSerializer


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

        # Проверяем, аутентифицирован ли пользователь
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Вы должны быть аутентифицированы, чтобы оставлять комментарии.")

        serializer.save(product=product, user=self.request.user)  # Передаём user


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
            'pages': page_numbers,
            'total_count': Product.objects.count(), # 👈 Добавил total_count сюда
            'products': data
        })

    def get_page_numbers(self, total_pages, current_page):
        """Генерирует список страниц для пагинации"""
        max_buttons = 5
        pages = []

        if total_pages <= max_buttons:
            pages = list(range(1, total_pages + 1))
        else:
            left = max(1, current_page - 2)
            right = min(total_pages, current_page + 2)

            if left > 2:
                pages = [1, "..."] + list(range(left, right + 1))
            else:
                pages = list(range(1, right + 1))

            if right < total_pages - 1:
                pages += ["...", total_pages]
            elif right == total_pages - 1:
                pages += [total_pages]

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

        Product.objects.filter(in_stock=0).delete()

        queryset = Product.objects.all()
        product_filters = self.request.session.get('product_filters')
        sort_by_price = self.request.session.get('sort_by_price')

        if product_filters:
            query_dict = QueryDict('', mutable=True)
            query_dict.update(product_filters)

            search_term = product_filters.get('search')
            if search_term:
                queryset = queryset.filter(
                    Q(title__icontains=search_term) |
                    Q(manufacturer__icontains=search_term) |
                    Q(model__icontains=search_term)
                )

            filterset = ProductFilterall(query_dict, queryset=queryset)
            queryset = filterset.qs

        if sort_by_price == "cheap":
            queryset = queryset.order_by(
                Case(
                    When(promotion__isnull=False, promotion__gt=0, then=F('promotion')),
                    default=F('price')
                ).asc()
            )
        elif sort_by_price == "expensive":
            queryset = queryset.order_by(
                Case(
                    When(promotion__isnull=False, promotion__gt=0, then=F('promotion')),
                    default=F('price')
                ).desc()
            )
        return queryset

    @swagger_auto_schema(
        operation_summary="Получение списка всех товаров",
        operation_description="Этот эндпоинт возвращает список товаров, применяя сохраненные фильтры из `/product/filter/`. Поддерживает пагинацию, поиск по названию и сортировку по цене. Сортировка учитывает акционные цены (`promotion`) если они есть.",
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="Поиск товаров по названию, производителю или модели",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="ordering",
                in_=openapi.IN_QUERY,
                description="Поле для сортировки (`price`, `-price` и др.)",
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
                description="Количество элементов на странице (например, 12, 24, 48)",
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
                            description="Список страниц для навигации (может содержать '...')"
                        ),
                        "total_count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Общее количество товаров, соответствующих фильтру"
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
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            format=openapi.FORMAT_URI
                                        ),
                                        description="Список URL изображений товара"
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
                                        description="Остаток товара на складе"
                                    ),
                                    "price": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Цена товара (или договорная)"
                                    ),
                                    "promotion": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="акции товаров(если нет то null)"
                                    ),
                                    "is_favorite": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Флаг: добавлен ли товар в избранное"
                                    ),
                                    "season": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Сезонность товара (`winter`, `summer`, `all_season`)"
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: "Ошибка запроса (например, неправильный формат фильтра)",
            500: "Внутренняя ошибка сервера"
        }
    )

    def get(self, request, *args, **kwargs):
        """
        Обрабатывает GET-запрос и применяет фильтрацию.
        """
        products = self.get_queryset()  # Получаем товары с фильтрацией

        # ✅ Применяем пагинацию
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response({
            'total_count': products.count(),
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
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        requested_flag = request.data.get("is_favorite")

        if requested_flag is not None:
            if requested_flag:
                product.is_favorite = True
                product.favorite_created_at = timezone.now()  # ✅ Всегда обновляем
            else:
                product.is_favorite = False
                product.favorite_created_at = None
        else:
            # Переключаем
            product.is_favorite = not product.is_favorite
            product.favorite_created_at = timezone.now() if product.is_favorite else None

        product.save()

        queryset = Product.objects.filter(is_favorite=True).order_by('-favorite_created_at')
        serializer = FavoriteProductListSerializer(queryset, many=True)
        total_favorites = queryset.count()

        return Response({
            "total_favorites": total_favorites,
            "favorites": serializer.data
        }, status=status.HTTP_200_OK)


class ProductSortView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Применить сортировку по цене",
        operation_description="Сохраняет выбранную сортировку товаров по цене ('cheap' или 'expensive') в сессии.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["sort_by_price"],
            properties={
                "sort_by_price": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["cheap", "expensive"],
                    description="Выбор сортировки: cheap - сначала дешевые, expensive - сначала дорогие"
                )
            }
        ),
        responses={
            200: openapi.Response(description="Сортировка применена"),
            400: openapi.Response(description="Ошибка запроса")
        }
    )
    def post(self, request, *args, **kwargs):
        sort_by_price = request.data.get("sort_by_price")

        if sort_by_price not in ("cheap", "expensive"):
            return Response({"error": "Invalid sort_by_price value"}, status=status.HTTP_400_BAD_REQUEST)

        request.session['sort_by_price'] = sort_by_price
        request.session.modified = True

        return Response({"message": "Sort by price saved", "sort_by_price": sort_by_price}, status=status.HTTP_200_OK)


class ProductFilterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Применить фильтры для поиска товаров",
        operation_description="Применяет выбранные фильтры к товарам, сохраняет отфильтрованные ID товаров и параметры фильтрации в сессии для последующего использования.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "season": openapi.Schema(type=openapi.TYPE_STRING, example="summer"),
                "manufacturer": openapi.Schema(type=openapi.TYPE_STRING, example="Michelin"),
                "tire_type": openapi.Schema(type=openapi.TYPE_STRING, example="suv"),
                "condition": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                "min_price": openapi.Schema(type=openapi.TYPE_NUMBER, example=2000),
                "max_price": openapi.Schema(type=openapi.TYPE_NUMBER, example=5000),
                "min_load_index": openapi.Schema(type=openapi.TYPE_INTEGER, example=80),
                "max_load_index": openapi.Schema(type=openapi.TYPE_INTEGER, example=100),
                "min_noise_level": openapi.Schema(type=openapi.TYPE_INTEGER, example=68),
                "max_noise_level": openapi.Schema(type=openapi.TYPE_INTEGER, example=75),
                "width": openapi.Schema(type=openapi.TYPE_STRING, example="205"),
                "profile": openapi.Schema(type=openapi.TYPE_STRING, example="55"),
                "diameter": openapi.Schema(type=openapi.TYPE_STRING, example="16"),
                "speed_index": openapi.Schema(type=openapi.TYPE_STRING, example="H"),
                "runflat": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                "off_road": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                "promotion": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
            }
        ),
        responses={
            200: openapi.Response(
                description="Фильтрация применена успешно",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "filtered_product_ids": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_INTEGER)
                        ),
                        "filter_data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        filters = request.data
        filtered_products = ProductFilterall(filters, queryset=Product.objects.all()).qs
        product_ids = list(filtered_products.values_list('id', flat=True))

        request.session["filtered_product_ids"] = product_ids
        request.session["product_filters"] = filters
        request.session.modified = True

        return Response({
            "message": "Фильтрация сохранена",
            "filtered_product_ids": product_ids,
            "filter_data": self.get_filter_data()
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Получить значения для фильтров",
        operation_description="Возвращает все возможные значения для фильтрации товаров.",
        responses={
            200: openapi.Response(
                description="Успешный ответ со списком доступных фильтров",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "filter_data": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return Response({
            "filter_data": self.get_filter_data()
        }, status=status.HTTP_200_OK)

    def get_filter_data(self):
        products_with_final_price = Product.objects.annotate(
            final_price=Case(
                When(promotion__gt=0, then=F("promotion")),
                default=F("price"),
                output_field=DecimalField()
            )
        )

        min_final_price = products_with_final_price.aggregate(min_price=Min("final_price"))["min_price"]
        max_final_price = products_with_final_price.aggregate(max_price=Max("final_price"))["max_price"]

        return {
            "seasons": Product.objects.values_list("season__value", flat=True).distinct(),
            "manufacturers": Product.objects.values_list("manufacturer", flat=True).distinct(),
            "tire_types": Product.objects.values_list("tire_type__value", flat=True).distinct(),
            "conditions": Product.objects.values_list("condition", flat=True).distinct(),
            "fuel_efficiency": dict(Product.FUEL_EFFICIENCY_CHOICES),
            "wet_grip": dict(Product.WET_GRIP_CHOICES),
            "min_price": min_final_price,
            "max_price": max_final_price,
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
class FilterDetailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Детали применённых фильтров ",
        operation_description="""
    Этот эндпоинт показывает, какие фильтры были применены ранее.
    Фильтры хранятся в сессии, устанавливаются через POST /product/filter/.

    """,
        responses={
            200: openapi.Response(
                description="Список товаров и примененные фильтры",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "applied_filters": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Применённые фильтры из сессии"
                        ),
                        "total_matched": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Количество совпавших товаров"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Фильтры не найдены в сессии"
            )
        },
        tags=["Product Filter"]
    )

    def get(self, request, *args, **kwargs):
        filters = request.session.get("product_filters")
        if not filters:
            return Response({"message": "Фильтры не найдены в сессии"}, status=404)

        # Получаем отфильтрованные товары
        filtered_qs = ProductFilterall(filters, queryset=Product.objects.all()).qs




        return Response({
            "applied_filters": filters,
            "total_matched": filtered_qs.count()
        }, status=200)

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        data = serializer.data

        is_negotiable = product.negotiable
        raw_price = product.price
        raw_promotion = product.promotion

        price_val = float(raw_price) if raw_price is not None else None
        promotion_val = float(raw_promotion) if raw_promotion is not None else None

        session_price = request.session.get(f"product_{product.id}_price", price_val)
        session_promotion = request.session.get(f"product_{product.id}_promotion", promotion_val)
        session_in_stock = request.session.get(f"product_{product.id}_in_stock", product.in_stock)
        session_count = request.session.get(f"product_{product.id}_count", 1)

        request.session.modified = True
        if session_count == 1:
            request.session[f"product_{product.id}_price"] = price_val
            request.session[f"product_{product.id}_promotion"] = promotion_val
            request.session[f"product_{product.id}_in_stock"] = product.in_stock

        # 🧠 логика для "Договорная"
        if is_negotiable:
            price = "Договорная"
        else:
            price = session_price if session_price is not None else price_val

        promotion = session_promotion if session_promotion is not None else promotion_val
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

        if similar_products.count() < 5 and product.price is not None:
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
                "is_favorite": p["is_favorite"],
                "season": p["season_value"],
                "image1": p.get("image", None),
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
                'body_type': product.body_type.label,
                'tire_type': product.tire_type.label
            },
            "title": data.get("title", product.title),
            "is_favorite": product.is_favorite,
            "image": data.get("image"),
            "promotion": promotion,
            "average_rating": data.get("average_rating", 0.0),
            "comments_count": product.comment_set.count(),
            "model_description": data.get("model_description", ""),
            "price": price,

            "negotiable": data.get("negotiable", False),
            "in_stock": in_stock,
            "warranty": data.get("warranty") or "",
            "count": session_count,
            "similar_products": similar_products_data,
        })

    def post(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        requested_flag = request.data.get("is_favorite")

        if requested_flag is not None:
            if requested_flag:
                product.is_favorite = True
                product.favorite_created_at = timezone.now()  # ✅ Всегда обновляем
            else:
                product.is_favorite = False
                product.favorite_created_at = None
        else:
            # Переключаем
            product.is_favorite = not product.is_favorite
            product.favorite_created_at = timezone.now() if product.is_favorite else None

        product.save()

        queryset = Product.objects.filter(is_favorite=True).order_by('-favorite_created_at')
        serializer = FavoriteProductListSerializer(queryset, many=True)
        total_favorites = queryset.count()

        return Response({
            "total_favorites": total_favorites,
            "favorites": serializer.data
        }, status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        product = self.get_object()
        count = request.data.get("count", 1)

        try:
            count = int(count)
            if count <= 0:
                return Response({"error": "Count must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid count value"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Фикс: безопасно работаем с None
        base_price = product.promotion or product.price
        session_price = float(base_price) * count if (base_price is not None and not product.negotiable) else None
        session_promotion = float(product.promotion) * count if product.promotion and not product.negotiable else None
        session_in_stock = product.in_stock if count == 1 else max(0, product.in_stock - count)

        request.session[f"product_{product.id}_count"] = count
        request.session[f"product_{product.id}_price"] = session_price
        request.session[f"product_{product.id}_promotion"] = session_promotion
        request.session[f"product_{product.id}_in_stock"] = session_in_stock
        request.session.modified = True

        return Response({
            "id": product.id,
            "price": session_price if session_price is not None else "Договорная",
            "promotion": session_promotion,
            "in_stock": session_in_stock,
            "count": count
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
    queryset = Comment.objects.all()

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        # Получаем все комментарии для данного продукта и сортируем их по дате (новые комментарии первыми)
        return Comment.objects.filter(product_id=product_id).order_by('-created_at')


class NewsCustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 6
    max_limit = None



class NewsListView(APIView):
    pagination_class = NewsCustomLimitOffsetPagination

    @swagger_auto_schema(
        operation_description="Получить список новостей (с пагинацией)",
        responses={
            200: openapi.Response(
                description="Пагинированный список новостей",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Общее количество новостей'),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True,
                                               description='Ссылка на следующую страницу'),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True,
                                                   description='Ссылка на предыдущую страницу'),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'news_image': openapi.Schema(type=openapi.TYPE_STRING),
                                    'news_title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'news_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'news_description': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            )
        }
    )

    def get(self, request):
        news = News.objects.all().order_by('-news_time')
        paginator = self.pagination_class()
        paginated_news = paginator.paginate_queryset(news, request, view=self)
        serializer = NewsSerializer(paginated_news, many=True)
        return paginator.get_paginated_response(serializer.data)


class NewsDetailView(APIView):
    @swagger_auto_schema(
        operation_description="Получить подробную информацию о новости по ID",
        responses={
            200: openapi.Response(
                description="Детали новости",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'news_image': openapi.Schema(type=openapi.TYPE_STRING),
                        'news_title': openapi.Schema(type=openapi.TYPE_STRING),
                        'news_time': openapi.Schema(type=openapi.TYPE_STRING),
                        'news_description': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: openapi.Response(description="Новость не найдена")
        }
    )

    def get(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        serializer = NewsDetailSerializer(news)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NewsCreateView(generics.CreateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Создание новости",
        operation_description="Создание новой новости с изображением (загрузка через файл).",
        request_body=NewsSerializer,
        responses={
            201: openapi.Response(
                description="Новость успешно создана",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "news_title": openapi.Schema(type=openapi.TYPE_STRING),
                        "news_time": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                        "news_description": openapi.Schema(type=openapi.TYPE_STRING),
                        "news_image": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибки при создании новости",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        tags=["News"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            news = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Создание нового товара",
        operation_description="""
    Создаёт новый товар для отображения в админке.

    - Обязательные поля: `title`, `image1`, `price` или `negotiable`, `season`, `tire_type`, `body_type`, `condition`, и базовые характеристики.
    - Если `negotiable = true`, то `price` и `promotion` не должен быть указан.
    - Если `negotiable = false`, то `price` обязателен.
    - Поля `image2` — `image7` являются необязательными.
    - ForeignKey поля ( `tire_type`, `body_type`) принимают `value` вместо `id`.
    - ForeignKey поля ( `season`, `condition`) принимают `id` вместо `value`.
    
    """,
        request_body=ProductCreateSerializer,
        responses={
            201: openapi.Response(
                description="Товар успешно создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=123),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Товар успешно создан")
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "non_field_errors": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Цена обязательна, если товар не договорной."]
                        )
                    },
                    additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                )
            )
        },
        tags=["Admin - Products"]
    )
    def post(self, request, *args, **kwargs):
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response({
                "success": True,
                "product_id": product.id,
                "message": "Товар успешно создан"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TireTypeAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Создание типа шины",
        operation_description="Принимает английское значение `value` и возвращает русский `label` (автоперевод).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["value"],
            properties={
                "value": openapi.Schema(type=openapi.TYPE_STRING,
                                        description="Английское значение, например: 'passenger'"),
            }
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "value": openapi.Schema(type=openapi.TYPE_STRING, example="passenger"),
                    "label": openapi.Schema(type=openapi.TYPE_STRING, example="пассажирский"),
                }
            ),
            400: "Ошибка валидации"
        },
        tags=["TireType"]
    )
    def post(self, request):
        serializer = TireTypeSerializer(data=request.data)
        if serializer.is_valid():
            tire_type = serializer.save()
            return Response({'value': tire_type.value, 'label': tire_type.label}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Получение всех типов шин",
        operation_description="Возвращает список всех типов шин с полями id, value и label.",
        responses={
            200: openapi.Response(
                description="Список типов шин",
                schema=TireTypeSerializer(many=True) #
            )
        },
        tags=["TireType"]
    )
    def get(self, request):
        queryset = TireType.objects.all()
        serializer = TireTypeSerializer(queryset, many=True)
        return Response(serializer.data)


class BodyTypeAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Создание типа кузова",
        operation_description="Принимает английское значение `value` и возвращает русский `label` (автоперевод).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["value"],
            properties={
                "value": openapi.Schema(type=openapi.TYPE_STRING, description="Английское значение, например: 'sedan'"),
            }
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "value": openapi.Schema(type=openapi.TYPE_STRING, example="sedan"),
                    "label": openapi.Schema(type=openapi.TYPE_STRING, example="седан"),
                }
            ),
            400: "Ошибка валидации"
        },
        tags=["BodyType"]
    )
    def post(self, request):
        serializer = BodyTypeSerializer(data=request.data)
        if serializer.is_valid():
            body_type = serializer.save()
            return Response({'value': body_type.value, 'label': body_type.label}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Получение всех типов кузова",
        operation_description="Возвращает список всех доступных типов кузова с полями id, value и label.",
        responses={
            200: openapi.Response(
                description="Список типов кузова",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            'value': openapi.Schema(type=openapi.TYPE_STRING, example='suv'),
                            'label': openapi.Schema(type=openapi.TYPE_STRING, example='внедорожник')
                        }
                    )
                )
            )
        },
        tags=["BodyType"]
    )
    def get(self, request):
        queryset = BodyType.objects.all()
        serializers = BodyTypeSerializer(queryset, many=True)
        return Response(serializers.data)


class ProductUpdateDeleteView(APIView):
    @swagger_auto_schema(
        operation_summary="Обновление полей товара",
        operation_description="Обновляет цену, договорность, акцию и наличие по ID",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена товара"),
                "negotiable": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Договорная цена"),
                "promotion": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена по акции"),
                "in_stock": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество на складе"),
            }
        ),
        responses={200: "Успешно обновлено", 404: "Товар не найден"},
        tags=["Product"]
    )
    def put(self, request, pk):
        product = get_object_or_404(Product, id=pk)

        negotiable = request.data.get("negotiable", product.negotiable)
        product.negotiable = negotiable

        if product.negotiable:
            product.price = None
            product.promotion = 0
        else:
            product.price = request.data.get("price", product.price)
            product.promotion = request.data.get("promotion", product.promotion)

        if "in_stock" in request.data:
            product.in_stock = request.data.get("in_stock")

        product.save()
        return Response({"success": "Товар успешно обновлён"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Удаление товара",
        operation_description="Удаляет товар по его ID",
        responses={204: "Удалено", 404: "Товар не найден"},
        tags=["Product"]
    )
    def delete(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


