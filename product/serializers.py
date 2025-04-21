
from rest_framework import serializers
from .models import Product, Comment, News
from drf_yasg import openapi
from django.db.models import Sum
from .utils import round_to_half
from product import models  # Тогда обращаться так: models.MyModel
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema

# Словарь для перевода с русского на английский
RUS_TO_ENG = {
    'Автомобильные шины': 'Car tires',
    'Грузовые машины': 'Trucks',
    'сельскохозяйственные шины': 'Agricultural tires',
    'Дорожно строительный': 'Road construction',
    'Аксессуары для шин, дисков и шиномонтажа': 'Tire, wheel, and tire service accessories',
    'Аккумуляторы': 'Batteries',
    'Автомасло': 'Motor oil',
    'Автоэлектроника': 'Car electronics',
    'Автохимия и автокосметика': 'Auto chemicals and car cosmetics',
    'Внешний декор, тюнинг, защита': 'Exterior decor, tuning, protection',
    'Инструменты и техническая помощь': 'Tools and technical assistance',
    'Компрессоры': 'Compressors',
}

class ProductCreateSerializer(serializers.ModelSerializer):
    image1 = serializers.ImageField(write_only=True, required=True)
    image2 = serializers.ImageField(write_only=True, required=False)
    image3 = serializers.ImageField(write_only=True, required=False)
    image4 = serializers.ImageField(write_only=True, required=False)
    image5 = serializers.ImageField(write_only=True, required=False)
    image6 = serializers.ImageField(write_only=True, required=False)
    image7 = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['title', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7' ,'price', 'negotiable', 'promotion', 'promotion_end_date', 'model_description', 'in_stock', 'profile', 'diameter', 'speed_index', 'load_index', 'load_index_for_double', 'manufacturer', 'model', 'generation', 'modification', 'promotionCategory', 'width', 'fuel_efficiency', 'wet_grip', 'external_noise_level', 'condition', 'season', 'tire_type', 'body_type', 'runflat', 'off_road', 'warranty' ]



    def create(self, validated_data):
        # Все изображения загружаем на Cloudinary вручную
        from cloudinary.uploader import upload

        for field in ['image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7']:
            if field in validated_data:
                upload_result = upload(validated_data[field])
                validated_data[field] = upload_result['public_id']

        return Product.objects.create(**validated_data)

class ProductSerializerHomepage(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    average_rating = serializers.SerializerMethodField(help_text="средний статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True, help_text="количество комментариев")
    image1 = serializers.SerializerMethodField(help_text="изображение шин #1")
    image2 = serializers.SerializerMethodField(help_text="изображение шин #2")
    image3 = serializers.SerializerMethodField(help_text="изображение шин #3")
    image4 = serializers.SerializerMethodField(help_text="изображение шин #4")
    image5 = serializers.SerializerMethodField(help_text="изображение шин #5")
    image6 = serializers.SerializerMethodField(help_text="изображение шин #6")
    image7 = serializers.SerializerMethodField(help_text="изображение шин #7")
    promotion_category = serializers.SerializerMethodField(help_text="это поля для дополнительной акции, еще на что действует кроме данного товара")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False, help_text="избранный в homepage который добавляет в избранные если равна к true.")
    title = serializers.CharField(max_length=100, help_text="названия шин")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="цена без учета скидки")

    class Meta:
        model = Product
        fields = [
            'product_Id', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'season', 'average_rating', 'comments_count',
            'title', 'in_stock', 'price', 'is_favorite', 'promotion_category'
        ]

    def get_promotion_category(self, obj):
        if obj.promotion_category:
            return obj.promotion_category.split(", ")  # Преобразуем строку в список
        return []

    def get_image1(self, obj):
        if obj.image1:
            return obj.image1.url
        return None

    def get_image2(self, obj):
        if obj.image2:
            return obj.image2.url
        return None


    def get_image3(self, obj):
        if obj.image3:
            return obj.image3.url
        return None

    def get_image4(self, obj):
        if obj.image4:
            return obj.image4.url
        return None

    def get_image5(self, obj):
        if obj.image5:
            return obj.image5.url
        return None

    def get_image6(self, obj):
        if obj.image6:
            return obj.image6.url
        return None

    def get_image7(self, obj):
        if obj.image7:
            return obj.image7.url
        return None


    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_average_rating(self, obj):
        comments = obj.comment_set.exclude(rating__isnull=True)  # Исключаем пустые значения рейтинга
        count = comments.count()

        if count == 0:
            return 0.0  # Если нет комментариев, возвращаем 0.0

        # Суммируем все рейтинги и вычисляем среднее
        total_rating = comments.aggregate(models.Sum("rating"))["rating__sum"] or 0
        average_rating = total_rating / count

        # Ограничиваем максимальное значение до 5.0
        average_rating = min(average_rating, 5.0)

        # Округляем до одного знака после запятой
        return round(average_rating, 1)


class FavoriteProductListSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id')
    image1 = serializers.SerializerMethodField(help_text="изображение шин #1")
    image2 = serializers.SerializerMethodField(help_text="изображение шин #2")
    image3 = serializers.SerializerMethodField(help_text="изображение шин #3")
    image4 = serializers.SerializerMethodField(help_text="изображение шин #4")
    image5 = serializers.SerializerMethodField(help_text="изображение шин #5")
    image6 = serializers.SerializerMethodField(help_text="изображение шин #6")
    image7 = serializers.SerializerMethodField(help_text="изображение шин #7")
    season = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField(help_text="средний статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True,
                                              help_text="количество комментариев")

    class Meta:
        model = Product
        fields = ['product_Id', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7',  'price', 'season', 'title', 'in_stock', 'is_favorite', 'average_rating', 'comments_count']

    def get_image1(self, obj):
        if obj.image1:
            return obj.image1.url
        return None

    def get_image2(self, obj):
        if obj.image2:
            return obj.image2.url
        return None

    def get_image3(self, obj):
        if obj.image3:
            return obj.image3.url
        return None

    def get_image4(self, obj):
        if obj.image4:
            return obj.image4.url
        return None

    def get_image5(self, obj):
        if obj.image5:
            return obj.image5.url
        return None

    def get_image6(self, obj):
        if obj.image6:
            return obj.image6.url
        return None

    def get_image7(self, obj):
        if obj.image7:
            return obj.image7.url
        return None

    def get_season(self, obj):
        if obj.season:
            return {
                "label": obj.season.label,
                "value": obj.season.value
            }
        return None




    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_average_rating(self, obj):
        comments = obj.comment_set.all()
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        average_rating = total_rating / len(comments)

        # Ограничиваем максимальное значение до 5.0
        average_rating = min(average_rating, 5.0)

        return round(average_rating, 1)


class CommentSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()  # Изменяем на product_id
    rating = serializers.DecimalField(max_digits=2, decimal_places=1)
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'product_id', 'comment', 'rating', 'created_at', 'username']

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Продукт с таким ID не найден.")
        return value

class ProductSerializerll(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    average_rating = serializers.SerializerMethodField(help_text="средний статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True, help_text="количество комментариев")
    image1 = serializers.SerializerMethodField(help_text="изображение шин #1")
    image2 = serializers.SerializerMethodField(help_text="изображение шин #2")
    image3 = serializers.SerializerMethodField(help_text="изображение шин #3")
    image4 = serializers.SerializerMethodField(help_text="изображение шин #4")
    image5 = serializers.SerializerMethodField(help_text="изображение шин #5")
    image6 = serializers.SerializerMethodField(help_text="изображение шин #6")
    image7 = serializers.SerializerMethodField(help_text="изображение шин #7")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False, help_text="избранный в каталоге который добавляет в избранные если равна к true.")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="цена без учета скидки")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    title = serializers.CharField(max_length=100, help_text="названия шины")

    class Meta:
        model = Product
        fields = ['product_Id', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'average_rating', 'comments_count', 'title', 'in_stock', 'price', 'is_favorite', "season"]

    # Swagger-описание для promotion_category
    promotion_category_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,  # Указываем, что это массив
        items=openapi.Items(type=openapi.TYPE_STRING),
        description="Список категорий акции, например: ['diski', 'tires']"
    )

    def get_season(self, obj):
        if obj.season:
            return obj.season.value  # Возвращаем значение label, а не id
        return None

    def get_image1(self, obj):
        if obj.image1:
            return obj.image1.url
        return None

    def get_image2(self, obj):
        if obj.image2:
            return obj.image2.url
        return None

    def get_image3(self, obj):
        if obj.image3:
            return obj.image3.url
        return None

    def get_image4(self, obj):
        if obj.image4:
            return obj.image4.url
        return None

    def get_image5(self, obj):
        if obj.image5:
            return obj.image5.url
        return None

    def get_image6(self, obj):
        if obj.image6:
            return obj.image6.url
        return None

    def get_image7(self, obj):
        if obj.image7:
            return obj.image7.url
        return None

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_average_rating(self, obj):
        comments = obj.comment_set.all()
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        average_rating = total_rating / len(comments)

        # Ограничиваем максимальное значение до 5.0
        average_rating = min(average_rating, 5.0)

        return round(average_rating, 1)


class ProductDetailSerializer(serializers.ModelSerializer):
    image1 = serializers.SerializerMethodField(help_text="изображение шин #1")
    image2 = serializers.SerializerMethodField(help_text="изображение шин #2")
    image3 = serializers.SerializerMethodField(help_text="изображение шин #3")
    image4 = serializers.SerializerMethodField(help_text="изображение шин #4")
    image5 = serializers.SerializerMethodField(help_text="изображение шин #5")
    image6 = serializers.SerializerMethodField(help_text="изображение шин #6")
    image7 = serializers.SerializerMethodField(help_text="изображение шин #7")
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True,
                                              help_text="количество комментариев")
    average_rating = serializers.SerializerMethodField()
    season_value = serializers.CharField(source="season.value", read_only=True)
    is_favorite = serializers.BooleanField(default=False,
                                           help_text="избранный в каталоге который добавляет в избранные если равна к true.")
    warranty = serializers.CharField(allow_blank=True, required=False)

    in_stock = serializers.IntegerField(help_text="количество шины в складе")

    class Meta:
        model = Product
        fields = ["id", "title", 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7',  "manufacturer", "in_stock", "model", "price", "season", "is_favorite", "width",
                  "profile", "diameter", "speed_index", "load_index", "load_index_for_double", "comments",
                  "average_rating", "model_description", "season_value", "warranty", 'comments_count',]

    def get_image1(self, obj):
        if obj.image1:
            return obj.image1.url
        return None

    def get_image2(self, obj):
        if obj.image2:
            return obj.image2.url
        return None

    def get_image3(self, obj):
        if obj.image3:
            return obj.image3.url
        return None

    def get_image4(self, obj):
        if obj.image4:
            return obj.image4.url
        return None

    def get_image5(self, obj):
        if obj.image5:
            return obj.image5.url
        return None

    def get_image6(self, obj):
        if obj.image6:
            return obj.image6.url
        return None

    def get_image7(self, obj):
        if obj.image7:
            return obj.image7.url
        return None

    def get_average_rating(self, obj):
        """Вычисляет средний рейтинг продукта на лету."""
        comments = obj.comment_set.all()
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        average_rating = total_rating / len(comments)

        # Ограничиваем максимальное значение до 5.0
        average_rating = min(average_rating, 5.0)

        return round(average_rating, 1)


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ["id", "news_image", "news_title", "news_time", "news_description"]
        extra_kwargs = {
            "news_description": {"write_only": True}
        }

class NewsDetailSerializer(serializers.ModelSerializer):
    related_news = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ['id', 'news_image', 'news_title', 'news_time', 'news_description', 'related_news']

    def get_related_news(self, obj):
        related_news = News.objects.filter(
            Q(news_title__icontains=obj.news_title) |
            Q(news_description__icontains=obj.news_description)
        ).exclude(id=obj.id).distinct()[:5]

        return NewsSerializer(related_news, many=True).data

