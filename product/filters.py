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
