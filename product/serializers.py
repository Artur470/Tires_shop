
from rest_framework import serializers
from .models import Product, Comment, News, Season, TireType, BodyType
from drf_yasg import openapi
from django.db.models import Sum
from .utils import round_to_half
from product import models  # Тогда обращаться так: models.MyModel
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from deep_translator import GoogleTranslator
from difflib import get_close_matches

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

BODY_TYPES_RUS_TO_ENG = {
    'Седан': 'Sedan',
    'Купе': 'Coupe',
    'Кабриолет / Конвертируемый': 'Convertible',
    'Родстер': 'Roadster',
    'Хэтчбек': 'Hatchback',
    'Лифтбэк': 'Liftback',
    'Фастбэк': 'Fastback',
    'Универсал': 'Station Wagon',
    'Кроссовер': 'Crossover',
    'Внедорожник (SUV)': 'Sport Utility Vehicle (SUV)',
    'Пикап': 'Pickup Truck',
    'Минивэн': 'Minivan',
    'Фургон / Вэн': 'Van',
    'Каблук (компактный фургон)': 'Panel Van',
    'Лимузин': 'Limousine',
    'Микроавтомобиль': 'Microcar',
    'Гранд турер (GT)': 'Grand Tourer (GT)',
    'Спортивный автомобиль': 'Sports Car',
    'Маслкар': 'Muscle Car',
    'Пони-кар': 'Pony Car',
    'Каммбэк': 'Kammback',
    'Тарга': 'Targa Top',
    'Тарпан': 'Tarpan',
    'Купе-кроссовер': 'Coupe-Crossover',
    'Седан-кроссовер': 'Sedan-Crossover',
    'Фургон с высоким потолком': 'High Roof Van',
    'Фургон с низким потолком': 'Low Roof Van',
    'Кемпер': 'Camper Van',
    'Автодом': 'Motorhome',
    'Трехколесный автомобиль': 'Three-Wheeler',
    'Электромобиль': 'Electric Car',
    'Гибридный автомобиль': 'Hybrid Car',
    'Водородный автомобиль': 'Hydrogen Car',
    'Автономный автомобиль': 'Self-Driving Car',
    'Грузовик': 'Truck',
    'Коммерческий автомобиль': 'Commercial Vehicle',
    'Специальный автомобиль': 'Special Purpose Vehicle',
}

TIRE_TYPES_RUS_TO_ENG = {
    'Фрикционные шины (липучка)': 'Friction tires (non-studded)',
    'Шипованные шины': 'Studded tires',
    'Туринговые шины': 'Touring tires',
    'Шоссейные шины': 'Highway tires',
    'Спортивные шины': 'Performance tires',
    'Грузовые шины': 'Truck tires',
    'Легковые шины': 'Passenger tires',
    'Внедорожные шины': 'Off-road tires',
    'Шины MT (грязевые)': 'Mud-terrain tires',
    'Шины AT (все местности)': 'All-terrain tires',
    'Радиальные шины': 'Radial tires',
    'Диагональные шины': 'Bias-ply tires',
    'Bias-belted шины': 'Bias-belted tires',
    'Камерные шины': 'Tube-type tires',
    'Бескамерные шины': 'Tubeless tires',
    'Run-flat шины': 'Run-flat tires',
    'Airless шины': 'Airless (Non-pneumatic) tires',
    'Трубчатые шины': 'Tubular tires',
    'Сельскохозяйственные шины': 'Agricultural tires',
    'Индустриальные шины': 'Industrial tires',
    'Шины для спецтехники': 'Special machinery tires',
    'Самогерметизирующиеся шины': 'Self-sealing tires',
    'Шины с низким сопротивлением качению': 'Low rolling resistance tires',
    'Асимметричные шины': 'Asymmetric tires',
    'Симметричные шины': 'Symmetric tires',
    'Направленные шины': 'Directional tires',
}

TIRE_ENG_TO_RUS = {v: k for k, v in TIRE_TYPES_RUS_TO_ENG.items()}
BODY_ENG_TO_RUS = {v: k for k, v in BODY_TYPES_RUS_TO_ENG.items()}



def fuzzy_translate(eng_value: str, dictionary: dict) -> str:
    matches = get_close_matches(eng_value, dictionary.keys(), n=1, cutoff=0.6)
    if not matches:
        raise serializers.ValidationError({"value": f"Не удалось найти похожее значение для '{eng_value}'"})
    return dictionary[matches[0]]

class TireTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TireType
        fields = ['id','value','label']

    def create(self, validated_data):
        value = validated_data['value']
        label = fuzzy_translate(value, TIRE_ENG_TO_RUS)
        return TireType.objects.create(value=value, label=label)



class BodyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyType
        fields = ['id', 'label', 'value']

    def create(self, validated_data):
        value = validated_data['value']
        label = fuzzy_translate(value, BODY_ENG_TO_RUS)
        return BodyType.objects.create(value=value, label=label)


class ForeignKeyByValueField(serializers.PrimaryKeyRelatedField):
    """
    Кастомное поле, чтобы принимать `value` вместо `id` в ForeignKey.
    """
    def __init__(self, **kwargs):
        self.model = kwargs.pop("model")
        self.value_field = kwargs.pop("value_field", "value")
        super().__init__(queryset=self.model.objects.all(), **kwargs)

    def to_internal_value(self, data):
        try:
            return self.model.objects.get(**{self.value_field: data})
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"{self.model.__name__} with {self.value_field}='{data}' not found.")

    def to_representation(self, obj):
        return getattr(obj, self.value_field)


class ProductCreateSerializer(serializers.ModelSerializer):
    image1 = serializers.ImageField(write_only=True, required=True)
    image2 = serializers.ImageField(write_only=True, required=False)
    image3 = serializers.ImageField(write_only=True, required=False)
    image4 = serializers.ImageField(write_only=True, required=False)
    image5 = serializers.ImageField(write_only=True, required=False)
    image6 = serializers.ImageField(write_only=True, required=False)
    image7 = serializers.ImageField(write_only=True, required=False)
    tire_type = ForeignKeyByValueField(model=TireType)
    body_type = ForeignKeyByValueField(model=BodyType)

    class Meta:
        model = Product
        fields = [
            'title', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7',
            'price', 'negotiable', 'promotion', 'promotion_end_date', 'model_description',
            'in_stock', 'profile', 'diameter', 'speed_index', 'load_index',
            'load_index_for_double', 'manufacturer', 'model', 'generation', 'modification',
            'promotionCategory', 'width', 'fuel_efficiency', 'wet_grip',
            'external_noise_level', 'condition', 'season', 'tire_type', 'body_type',
            'runflat', 'off_road', 'warranty'
        ]

    def validate(self, attrs):
        negotiable = attrs.get("negotiable", False)
        price = attrs.get("price")

        if negotiable and price:
            raise serializers.ValidationError("Нельзя указывать цену, если товар договорной.")

        if not negotiable and not price:
            raise serializers.ValidationError("Цена обязательна, если товар не договорной.")

        return attrs

    def create(self, validated_data):
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
    image = serializers.SerializerMethodField(help_text="Словарь всех изображений шин")
    promotion_category = serializers.SerializerMethodField(help_text="это поля для дополнительной акции, еще на что действует кроме данного товара")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False, help_text="избранный в homepage который добавляет в избранные если равна к true.")
    title = serializers.CharField(max_length=100, help_text="названия шин")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    price = serializers.SerializerMethodField(help_text="Цена или 'Договорная'")


    class Meta:
        model = Product
        fields = [
            'product_Id', 'image', 'season', 'average_rating', 'comments_count',
            'title', 'in_stock', 'price', 'is_favorite', 'promotion_category', 'negotiable'
        ]

    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None

    def get_promotion_category(self, obj):
        if obj.promotionCategory:
            return obj.promotionCategory.split(", ")  # Преобразуем строку в список
        return []

    def get_image(self, obj):
        return [
            obj.image1.url if obj.image1 else None,
            obj.image2.url if obj.image2 else None,
            obj.image3.url if obj.image3 else None,
            obj.image4.url if obj.image4 else None,
            obj.image5.url if obj.image5 else None,
            obj.image6.url if obj.image6 else None,
            obj.image7.url if obj.image7 else None,
        ]

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_average_rating(self, obj):
        comments = obj.comment_set.exclude(rating__isnull=True)  # Исключаем пустые значения рейтинга
        count = comments.count()

        if count == 0:
            return 0.0  # Если нет комментариев, возвращаем 0.0

        # Суммируем все рейтинги и вычисляем среднее
        total_rating = comments.aggregate(total=Sum("rating"))["total"] or 0
        average_rating = total_rating / count

        # Ограничиваем максимальное значение до 5.0
        average_rating = min(average_rating, 5.0)

        # Округляем до одного знака после запятой
        return round(average_rating, 1)


    def get_season(self, obj):
        if obj.season:
            return obj.season.value
        return None

class FavoriteProductListSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id')
    image = serializers.SerializerMethodField(help_text="Словарь всех изображений шин")
    season = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField(help_text="средний статистический рейтинг")
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True,
                                              help_text="количество комментариев")
    price = serializers.SerializerMethodField(help_text="Цена или 'Договорная'")
    class Meta:
        model = Product
        fields = ['product_Id', 'image', 'price','promotion', 'negotiable', 'season', 'title', 'in_stock', 'is_favorite', 'average_rating', 'comments_count']

    def get_image(self, obj):
        return [
            obj.image1.url if obj.image1 else None,
            obj.image2.url if obj.image2 else None,
            obj.image3.url if obj.image3 else None,
            obj.image4.url if obj.image4 else None,
            obj.image5.url if obj.image5 else None,
            obj.image6.url if obj.image6 else None,
            obj.image7.url if obj.image7 else None,
        ]

    def get_season(self, obj):
        if obj.season:
            return obj.season.value  # Возвращаем значение label, а не id
        return None

    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None

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
    image = serializers.SerializerMethodField(help_text="Словарь всех изображений шин")
    season = serializers.SerializerMethodField(help_text="Сезонность шин: лето, зима, всесезонные.")
    is_favorite = serializers.BooleanField(default=False, help_text="избранный в каталоге который добавляет в избранные если равна к true.")
    price = serializers.SerializerMethodField(help_text="Цена или 'Договорная'")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    title = serializers.CharField(max_length=100, help_text="названия шины")

    class Meta:
        model = Product
        fields = ['product_Id', "image", 'average_rating', 'comments_count', 'negotiable', 'title', 'in_stock', 'price', 'promotion', 'is_favorite', "season"]


    promotion_category_schema = openapi.Schema(
        type=openapi.TYPE_ARRAY,  # Указываем, что это массив
        items=openapi.Items(type=openapi.TYPE_STRING),
        description="Список категорий акции, например: ['diski', 'tires']"
    )

    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None


    def get_season(self, obj):
        if obj.season:
            return obj.season.value  # Возвращаем значение label, а не id
        return None

    def get_image(self, obj):
        return [
            obj.image1.url if obj.image1 else None,
            obj.image2.url if obj.image2 else None,
            obj.image3.url if obj.image3 else None,
            obj.image4.url if obj.image4 else None,
            obj.image5.url if obj.image5 else None,
            obj.image6.url if obj.image6 else None,
            obj.image7.url if obj.image7 else None,
        ]

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

class ProductAutoCompleteSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id')
    average_rating = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    season = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'product_Id', 'image', 'average_rating', 'comments_count',
            'negotiable', 'title', 'in_stock', 'price', 'promotion', 'season'
        ]

    def get_image(self, obj):
        return [
            obj.image1.url if obj.image1 else None,
            obj.image2.url if obj.image2 else None,
            obj.image3.url if obj.image3 else None,
            obj.image4.url if obj.image4 else None,
            obj.image5.url if obj.image5 else None,
            obj.image6.url if obj.image6 else None,
            obj.image7.url if obj.image7 else None,
        ]

    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None

    def get_season(self, obj):
        return obj.season.value if obj.season else None

    def get_average_rating(self, obj):
        comments = obj.comment_set.all()
        if not comments:
            return 0.0
        total_rating = sum(comment.rating for comment in comments)
        average_rating = total_rating / len(comments)


        average_rating = min(average_rating, 5.0)

        return round(average_rating, 1)

    def get_comments_count(self, obj):
        return getattr(obj.comment_set, "count", lambda: 0)()

class ProductDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(help_text="Словарь всех изображений шин")
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True,
                                              help_text="количество комментариев")
    average_rating = serializers.SerializerMethodField()
    season_value = serializers.CharField(source="season.value", read_only=True)
    is_favorite = serializers.BooleanField(default=False,
                                           help_text="избранный в каталоге который добавляет в избранные если равна к true.")
    warranty = serializers.CharField(allow_blank=True, required=False)
    price = serializers.SerializerMethodField(help_text="Цена или 'Договорная'")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")

    class Meta:
        model = Product
        fields = ["id", "title", 'image',  "manufacturer", "in_stock", "model", "price", "season", "is_favorite", "width",
                  "profile", "diameter", "speed_index", "load_index", "load_index_for_double", "comments", "negotiable",
                  "average_rating", "model_description", "season_value", "warranty", 'comments_count', 'body_type', 'tire_type']

    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None

    def get_image(self, obj):
        return [
            obj.image1.url if obj.image1 else None,
            obj.image2.url if obj.image2 else None,
            obj.image3.url if obj.image3 else None,
            obj.image4.url if obj.image4 else None,
            obj.image5.url if obj.image5 else None,
            obj.image6.url if obj.image6 else None,
            obj.image7.url if obj.image7 else None,
        ]

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
    news_image1 = serializers.ImageField(write_only=True)
    news_image2 = serializers.ImageField(write_only=True, required=False)
    news_image3 = serializers.ImageField(write_only=True, required=False)
    news_image4 = serializers.ImageField(write_only=True, required=False)
    news_image5 = serializers.ImageField(write_only=True, required=False)
    news_image6 = serializers.ImageField(write_only=True, required=False)
    news_image7 = serializers.ImageField(write_only=True, required=False)
    news_image = serializers.SerializerMethodField(help_text="Список URL изображений")

    class Meta:
        model = News
        fields = [
            "id", "news_title", "news_time", "news_description", "news_image",
            "news_image1", "news_image2", "news_image3", "news_image4",
            "news_image5", "news_image6", "news_image7",
        ]

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop("exclude_fields", [])
        super().__init__(*args, **kwargs)
        for field in exclude_fields:
            self.fields.pop(field, None)

    def get_news_image(self, obj):
        return [
            obj.news_image1.url if obj.news_image1 else None,
            obj.news_image2.url if obj.news_image2 else None,
            obj.news_image3.url if obj.news_image3 else None,
            obj.news_image4.url if obj.news_image4 else None,
            obj.news_image5.url if obj.news_image5 else None,
            obj.news_image6.url if obj.news_image6 else None,
            obj.news_image7.url if obj.news_image7 else None,
        ]

    def create(self, validated_data):
        return News.objects.create(**validated_data)
class NewsDetailSerializer(serializers.ModelSerializer):
    related_news = serializers.SerializerMethodField()

    news_image = serializers.SerializerMethodField(help_text="Словарь всех изображений новостей")


    class Meta:
        model = News
        fields = ['id', 'news_image', 'news_title', 'news_time', 'news_description', 'related_news']

    def get_related_news(self, obj):
        related_news = News.objects.filter(
            Q(news_title__icontains=obj.news_title) |
            Q(news_description__icontains=obj.news_description)
        ).exclude(id=obj.id).distinct()[:5]

        return NewsSerializer(related_news, many=True).data

    def get_news_image(self, obj):
        return [
            obj.news_image1.url if obj.news_image1 else None,
            obj.news_image2.url if obj.news_image2 else None,
            obj.news_image3.url if obj.news_image3 else None,
            obj.news_image4.url if obj.news_image4 else None,
            obj.news_image5.url if obj.news_image5 else None,
            obj.news_image6.url if obj.news_image6 else None,
            obj.news_image7.url if obj.news_image7 else None,
        ]




