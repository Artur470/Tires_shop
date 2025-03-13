
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
    product_Id = serializers.IntegerField(source='id')
    average_rating = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True)
    image = serializers.SerializerMethodField()
    promotion_category = serializers.SerializerMethodField()

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
        fields = ['product_Id', 'image', 'price', 'seasonality', 'title', 'inStock', 'is_favorite']

class CommentSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())


    class Meta:
        model = Comment
        fields = ['id', 'product', 'comment', 'rating', 'created_at']

    def validate_product(self, value):
        if isinstance(value, Product):  # Если передали объект, берем его ID
            value = value.id
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Такого продукта не существует")
        return value


class ProductSerializerll(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id')
    average_rating = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True)
    image = serializers.SerializerMethodField()
    season = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['product_Id', 'image',  'average_rating', 'comments_count',
            'title', 'in_stock', 'price', 'is_favorite', "season",]


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
        return obj.average_rating



    def get_average_rating(self, obj):

        comments = obj.comment_set.all()
        from .utils import round_to_half
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        return round_to_half(total_rating / len(comments))


