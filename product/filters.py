import django_filters
from .models import Product, BodyType

# Словарь соответствия: ключ – value (англ.), значение – label (рус.)
from django.db.models import Q
import django_filters

BODY_TYPE_CHOICES = {
    "sedan": "Седан",
    "hatchback": "Хэтчбек",
    "liftback": "Лифтбек",
    "coupe": "Купе",
    "cabriolet": "Кабриолет",
    "convertible": "Кабриолет",
    "roadster": "Родстер",
    "targa": "Тарга",
    "limousine": "Лимузин",
    "universal": "Универсал",
    "station_wagon": "Универсал",
    "shooting_brake": "Шутинг-брейк",
    "crossover": "Кроссовер",
    "suv": "Внедорожник",
    "jeep": "Джип",
    "pickup": "Пикап",
    "minivan": "Минивэн",
    "microvan": "Микровэн",
    "van": "Фургон",
    "cargo_van": "Грузовой фургон",
    "passenger_van": "Пассажирский фургон",
    "bus": "Автобус",
    "truck": "Грузовик",
    "semi_truck": "Тягач",
    "tow_truck": "Эвакуатор",
    "flatbed_truck": "Бортовой грузовик",
    "box_truck": "Фургон",
    "dump_truck": "Самосвал",
    "tank_truck": "Цистерна",
    "garbage_truck": "Мусоровоз",
    "panel_van": "Цельнометаллический фургон",
    "combi": "Комби",
    "buggy": "Багги",
    "quad": "Квадроцикл",
    "trike": "Трайк",
    "motorcycle": "Мотоцикл",
    "atv": "Вездеход",
    "snowmobile": "Снегоход",
}

class ProductFilter(django_filters.FilterSet):
    manufacturer = django_filters.CharFilter(field_name="manufacturer", lookup_expr="icontains")
    model = django_filters.CharFilter(field_name="model", lookup_expr="icontains")
    generation = django_filters.CharFilter(field_name="generation", lookup_expr="icontains")
    modification = django_filters.CharFilter(field_name="modification", lookup_expr="icontains")
    body_type = django_filters.CharFilter(field_name='body_type', method='filter_by_body_type', label='Тип кузова')

    class Meta:
        model = Product
        fields = ['manufacturer', 'model', 'generation', 'modification', 'body_type']

    def filter_by_body_type(self, queryset, name, value):
        """
        Фильтруем товары по русскому названию body_type,
        конвертируя его в английское перед поиском.
        """
        value = value.strip().lower()  # Приводим к нижнему регистру

        # Словарь для перевода русского названия в английское
        reverse_body_type_choices = {rus.lower(): eng for eng, rus in BODY_TYPE_CHOICES.items()}

        # Если значение существует в словаре (это русский текст)
        if value in reverse_body_type_choices:
            value = reverse_body_type_choices[value]  # Переводим русское название в английское

        # Фильтруем товары по связанному полю body_type__value
        return queryset.filter(body_type__value=value)

class ProductFilterall(django_filters.FilterSet):
    # Для фильтрации по season, manufacturer, tire_type и другим ForeignKey полям
    season = django_filters.CharFilter(method="filter_season")
    manufacturer = django_filters.CharFilter(field_name='manufacturer', lookup_expr='exact')
    tire_type = django_filters.CharFilter(field_name='tire_type__value', lookup_expr='exact')
    condition = django_filters.CharFilter(field_name='condition__value', lookup_expr='exact')

    # Для числовых фильтров
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_load_index = django_filters.NumberFilter(field_name='load_index', lookup_expr='gte')
    max_load_index = django_filters.NumberFilter(field_name='load_index', lookup_expr='lte')
    min_noise_level = django_filters.NumberFilter(field_name='external_noise_level', lookup_expr='gte')
    max_noise_level = django_filters.NumberFilter(field_name='external_noise_level', lookup_expr='lte')

    # Для фильтрации по обычным полям
    width = django_filters.CharFilter(field_name='width', lookup_expr='exact')
    profile = django_filters.CharFilter(field_name='profile', lookup_expr='exact')
    diameter = django_filters.CharFilter(field_name='diameter', lookup_expr='exact')
    speed_index = django_filters.CharFilter(field_name='speed_index', lookup_expr='exact')

    # Для фильтрации по boolean полям
    runflat = django_filters.BooleanFilter(field_name='runflat')
    off_road = django_filters.BooleanFilter(field_name='off_road')

    # Кастомный фильтр для поля promotion (проверка на наличие акции)
    promotion = django_filters.BooleanFilter(field_name='promotion', method='filter_promotion')


    class Meta:
        model = Product
        fields = ['season', 'manufacturer', 'tire_type', 'condition', 'min_price', 'max_price',
                  'min_load_index', 'max_load_index', 'min_noise_level', 'max_noise_level',
                  'width', 'profile', 'diameter', 'speed_index', 'runflat', 'off_road', 'promotion']

    def filter_promotion(self, queryset, name, value):
        """
        Кастомная фильтрация для поля 'promotion'.
        Если value = True, то показываем товары с акциями (promotion > 0).
        Если value = False, то показываем товары без акции (promotion <= 0).
        """
        if value is True:
            return queryset.filter(promotion__gt=0)  # Только товары с акцией
        elif value is False:
            return queryset.filter(promotion__lte=0)  # Только товары без акции
        return queryset

    def filter_season(self, queryset, name, value):
        """ Фильтрация товаров по сезону """
        if value == "all_season":
            return queryset.filter(season__value="all_season")  # Фильтруем только товары с сезоном "все сезоны"
        return queryset.filter(season__value=value)  # Обычная фильтрация для других сезонов
