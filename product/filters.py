import django_filters
from .models import Product

# Словарь соответствия: ключ – value (англ.), значение – label (рус.)
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
    # Фильтрация по body_type через кастомный метод
    body_type = django_filters.CharFilter(method='filter_body_type')
    category_value = django_filters.CharFilter(field_name='category__value', lookup_expr='icontains',
                                               label='Категория (value)')

    class Meta:
        model = Product
        fields = ['manufacturer', 'model', 'generation', 'modification', 'body_type',  'category_value']

    def filter_body_type(self, queryset, name, value):
        lower_value = value.lower()
        # Если значение передано на английском (value), то переводим его в русское название (label)
        if lower_value in BODY_TYPE_CHOICES:
            russian_label = BODY_TYPE_CHOICES[lower_value]
            return queryset.filter(body_type__iexact=russian_label)
        # Если значение не найдено в словаре, пробуем фильтровать напрямую по переданному значению
        return queryset.filter(body_type__iexact=value)



class ProductFilterall(django_filters.FilterSet):
    # Фильтр по цене
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # Фильтры по обычным полям (`CharField`)
    width = django_filters.CharFilter(field_name="width", lookup_expr="exact")
    profile = django_filters.CharFilter(field_name="profile", lookup_expr="exact")
    diameter = django_filters.CharFilter(field_name="diameter", lookup_expr="exact")
    speed_index = django_filters.CharFilter(field_name="speed_index", lookup_expr="exact")

    # Фильтры по числовым полям (`IntegerField`)
    load_index_min = django_filters.NumberFilter(field_name="load_index", lookup_expr="gte")
    load_index_max = django_filters.NumberFilter(field_name="load_index", lookup_expr="lte")
    external_noise_level_min = django_filters.NumberFilter(field_name=" external_noise_level ", lookup_expr="gte")
    external_noise_level_max = django_filters.NumberFilter(field_name=" external_noise_level ", lookup_expr="lte")

    # Фильтры по `ForeignKey` (ищем через `value`)
    manufacturer = django_filters.CharFilter(field_name="manufacturer__value", lookup_expr="exact")
    season = django_filters.CharFilter(field_name="season__value", lookup_expr="exact")
    tire_type = django_filters.CharFilter(field_name="tire_type__value", lookup_expr="exact")
    condition = django_filters.CharFilter(field_name="condition__value", lookup_expr="exact")

    # Фильтры по `choices`
    fuel_efficiency = django_filters.ChoiceFilter(field_name="fuel_efficiency", choices=Product.FUEL_EFFICIENCY_CHOICES)
    wet_grip = django_filters.ChoiceFilter(field_name="wet_grip", choices=Product.WET_GRIP_CHOICES)

    # Фильтры по `BooleanField`
    runflat = django_filters.BooleanFilter(field_name="runflat")
    off_road = django_filters.BooleanFilter(field_name="off_road")

    promotion = django_filters.BooleanFilter(method='filter_promotion')


    def filter_promotion(self, queryset, name, value):
        if value:  # Если promotion=True, фильтруем товары с акциями
            return queryset.filter(promotion__gt=0)  # Показываем товары, где promotion > 0
        else:  # Если promotion=False или не передано, возвращаем все товары
            return queryset


    class Meta:
        model = Product
        fields = [
            "price_min", "price_max",
            "width", "profile", "diameter", "speed_index",
            "load_index_min", "load_index_max",
            "external_noise_level_min", "external_noise_level_max",
            "manufacturer", "season", "tire_type",
            "condition",
            "fuel_efficiency", "wet_grip",
            "promotion", "runflat", "off_road",
        ]
