from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from django.db.models import Count, Avg, F
import requests
from drf_yasg.utils import swagger_auto_schema
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

from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Category
from .serializers import CategoriesSerializer
import logging
from rest_framework.views import APIView
from .models import Product, Category, Comment
from .serializers import ProductSerializerHomepage, CategoriesSerializer,  FavoriteProductListSerializer  , CommentSerializer, ProductSerializerll
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
from .filters import ProductFilterall
from django_filters.rest_framework import DjangoFilterBackend
logger = logging.getLogger(__name__)



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
    search_fields = ['title', ]

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
                "average_rating": str(product.average_rating),
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

        # Доступные фильтры
        filters_data = {
            "manufacturers": list(Product.objects.values_list("manufacturer", flat=True).distinct()),
            "models": list(Product.objects.values_list("model", flat=True).distinct()),
            "generations": list(Product.objects.values_list("generation", flat=True).distinct()),
            "modifications": list(Product.objects.values_list("modification", flat=True).distinct()),


        }

        # Создание данных для главной страницы без "favorites"
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
    """
    serializer_class = ProductSerializerll
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title']
    ordering_fields = ['price']  # Позволяем сортировать по цене
    ordering = ['id']  # Фиксируем порядок по ID

    def get_queryset(self):
        return Product.objects.all().order_by('id')  # Гарантируем неизменяемый порядок

    @swagger_auto_schema(
        tags=['Homepage'],
        operation_summary="Получить список всех товаров",
        operation_description="Этот эндпоинт позволяет получить список всех товаров в базе данных с возможностью пагинации, фильтрации и поиска по названию.",
        responses={
            200: openapi.Response(
                description="Список товаров",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Общее количество товаров"),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'product_Id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара"),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING, description="Название товара"),
                                    'image': openapi.Schema(type=openapi.TYPE_STRING, description="URL изображения товара"),
                                    'price': openapi.Schema(type=openapi.TYPE_STRING, description="Цена товара"),
                                    'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Статус избранного"),
                                    'season': openapi.Schema(type=openapi.TYPE_STRING, description="Сезон товара"),
                                    'average_rating': openapi.Schema(type=openapi.TYPE_NUMBER, description="Средний рейтинг товара"),
                                    'comments_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество комментариев")
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка: некорректные параметры запроса",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Описание ошибки")
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        products = self.get_queryset()

        # Применяем пагинацию
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Без пагинации возвращаем полный список товаров
        serializer = self.get_serializer(products, many=True)
        return Response({
            'total_count': products.count(),
            'results': serializer.data
        })


    @swagger_auto_schema(
        tags=['Homepage'],
        operation_summary="Добавить товар в избранное",
        operation_description="Этот эндпоинт обновляет статус товара в избранном (true/false).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара"),
                'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="True/False — в избранное")
            },
            required=['product_id', 'is_favorite']
        ),
        responses={
            200: openapi.Response(
                description="Обновленный товар",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара"),
                        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Название товара"),
                        'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Статус избранного")
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка: отсутствуют обязательные параметры",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Описание ошибки")}
                )
            )
        }
    )
    def post(self, request):
        product_id = request.data.get('product_id')
        is_favorite = request.data.get('is_favorite')

        # Проверка на валидность входных данных
        if not isinstance(product_id, int) or not isinstance(is_favorite, bool):
            return Response({"detail": "Некорректные данные. product_id должен быть числом, is_favorite — true/false."}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем продукт по ID
        product = get_object_or_404(Product, id=product_id)

        # Обновляем статус избранного
        product.is_favorite = is_favorite
        product.save(update_fields=['is_favorite'])  # Обновляем только is_favorite

        return Response({
            "product_id": product.id,
            "title": product.title,
            "is_favorite": product.is_favorite
        }, status=status.HTTP_200_OK)
