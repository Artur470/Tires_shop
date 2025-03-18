
from rest_framework import serializers
from .models import Product, Category, Comment
from drf_yasg import openapi
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


class CategoriesSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    value = serializers.CharField(required=False)  # Делаем value необязательным

    class Meta:
        model = Category
        fields = ['id','label', 'value']

    def create(self, validated_data):
        if 'value' not in validated_data or not validated_data['value']:
            label = validated_data['label']
            # Переводим label на английский
            validated_data['value'] = RUS_TO_ENG.get(label, label)  # Если нет перевода, оставляем label как есть
        return super().create(validated_data)

class ProductSerializerHomepage(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    average_rating = serializers.SerializerMethodField(help_text="среднее статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True, help_text="количество комментариев")
    image = serializers.SerializerMethodField(help_text="изображение шин")
    promotion_category = serializers.SerializerMethodField(help_text="это поля для допалнительного акция еще на что действует кроме данного товара")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False,
                                           help_text="избранный в homepage который добавляет в избранные если равна к true.")
    title = serializers.CharField(max_length=100, help_text="названия шин")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="цена без учета скидки")


    class Meta:
        model = Product
        fields = [
            'product_Id', 'image', 'season', 'average_rating', 'comments_count',
            'title', 'in_stock', 'price', 'is_favorite', 'promotion_category'
        ]

    def get_promotion_category(self, obj):
        if obj.promotion_category:
            return obj.promotion_category.split(", ")  # Преобразуем строку в список
        return []

    # Swagger-описание для promotion_category
    promotion_category_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,  # Указываем, что это массив
        items=openapi.Items(type=openapi.TYPE_STRING),
        description="Список категорий акции, например: ['diski', 'tires']"
    )
    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_average_rating(self, obj):
        return obj.average_rating



    def get_average_rating(self, obj):

        comments = obj.comment_set.all()
        from .utils import round_to_half
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        return round_to_half(total_rating / len(comments))




class FavoriteProductListSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id')

    class Meta:
        model = Product
        fields = ['product_Id', 'image', 'price', 'season', 'title', 'in_stock', 'is_favorite']


class CommentSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()  # Изменяем на product_id

    class Meta:
        model = Comment
        fields = ['id', 'product_id', 'comment', 'rating', 'created_at']

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Продукт с таким ID не найден.")
        return value

class ProductSerializerll(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    average_rating = serializers.SerializerMethodField(help_text="средний статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True, help_text="количество комментариев")
    image = serializers.SerializerMethodField(help_text="изображение шин")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False, help_text="избранный в каталоге который добавляет в избранные если равна к true.")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="цена без учета скидки")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    title = serializers.CharField(max_length=100, help_text="названия шины")

    class Meta:
        model = Product
        fields = ['product_Id', 'image', 'average_rating', 'comments_count', 'title', 'in_stock', 'price', 'is_favorite', "season"]

    # Swagger-описание для promotion_category
    promotion_category_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,  # Указываем, что это массив
        items=openapi.Items(type=openapi.TYPE_STRING),
        description="Список категорий акции, например: ['diski', 'tires']"
    )

    def get_season(self, obj):
        if obj.season:
            return obj.season.label  # Возвращаем значение label, а не id
        return None

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_average_rating(self, obj):
        comments = obj.comment_set.all()
        from .utils import round_to_half
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        return round_to_half(total_rating / len(comments))


class ProductDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    season_label = serializers.CharField(source="season.label", read_only=True)
    condition_label = serializers.CharField(source="condition.label", read_only=True)
    tire_type_label = serializers.CharField(source="tire_type.label", read_only=True)
    body_type_label = serializers.CharField(source="body_type.label", read_only=True)
    category_label = serializers.CharField(source="category.label", read_only=True)
    category_value = serializers.CharField(source="category.value", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "title", "manufacturer", "model", "price", "season_label", "condition_label",
            "tire_type_label", "body_type_label", "category_label", "category_value", "is_favorite",
            "width", "profile", "diameter", "speed_index", "load_index", "load_index_for_double",
            "image_url", "comments", "average_rating", "model_description"
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_comments(self, obj):
        return [{"comment": c.comment, "rating": c.rating, "created_at": c.created_at} for c in obj.comment_set.all()]

    def get_average_rating(self, obj):
        comments = obj.comment_set.all()
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        return round(total_rating / len(comments), 1)
