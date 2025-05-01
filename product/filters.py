import django_filters
from .models import Product, BodyType
from django.db.models import ExpressionWrapper, F, fields
from django.db.models.functions import Coalesce
from django.db.models import DecimalField
from django.db.models import Case, When, F, DecimalField
# Словарь соответствия: ключ – value (англ.), значение – label (рус.)
from django.db.models import Q
from django_filters import BaseInFilter, BooleanFilter
from django.db.models import Case, When, Value, F, DecimalField
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



class BooleanFlexibleFilter(django_filters.Filter):
    def filter(self, qs, value):
        if value is None:
            return qs

        field = self.field_name  # <-- используем текущее поле

        if isinstance(value, list):
            queries = []
            for val in value:
                if val in (True, 'true', 'True', 1, '1'):
                    queries.append(qs.filter(**{f"{field}": True}))
                elif val in (False, 'false', 'False', 0, '0'):
                    queries.append(qs.filter(**{f"{field}": False}))
            if queries:
                result = queries[0]
                for q in queries[1:]:
                    result = result.union(q)
                return result

        if value in (True, 'true', 'True', 1, '1'):
            return qs.filter(**{f"{field}": True})
        elif value in (False, 'false', 'False', 0, '0'):
            return qs.filter(**{f"{field}": False})
        return qs

class ProductFilterall(django_filters.FilterSet):
    season = django_filters.CharFilter(method="filter_season")
    manufacturer = django_filters.CharFilter(field_name='manufacturer', lookup_expr='exact')
    tire_type = django_filters.CharFilter(field_name='tire_type__value', lookup_expr='exact')


    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')
    min_load_index = django_filters.NumberFilter(field_name='load_index', lookup_expr='gte')
    max_load_index = django_filters.NumberFilter(field_name='load_index', lookup_expr='lte')
    min_noise_level = django_filters.NumberFilter(field_name='external_noise_level', lookup_expr='gte')
    max_noise_level = django_filters.NumberFilter(field_name='external_noise_level', lookup_expr='lte')

    width = django_filters.CharFilter(field_name='width', lookup_expr='exact')
    profile = django_filters.CharFilter(field_name='profile', lookup_expr='exact')
    diameter = django_filters.CharFilter(field_name='diameter', lookup_expr='exact')
    speed_index = django_filters.CharFilter(field_name='speed_index', lookup_expr='exact')

    runflat = BooleanFlexibleFilter(field_name='runflat')
    off_road = BooleanFlexibleFilter(field_name='off_road')
    condition = BooleanFlexibleFilter(field_name='condition')
    promotion = django_filters.CharFilter(method='filter_promotion')
    sort_by_price = django_filters.CharFilter(method='filter_sort_by_price')

    class Meta:
        model = Product
        fields = ['season', 'manufacturer', 'tire_type', 'condition',
                  'min_load_index', 'max_load_index', 'min_noise_level', 'max_noise_level',
                  'width', 'profile', 'diameter', 'speed_index', 'runflat', 'off_road', 'promotion']

    def filter_promotion(self, queryset, name, value):
        true_vals = ['true', '1', True, 1]
        false_vals = ['false', '0', False, 0]

        if isinstance(value, list):
            queries = []
            for val in value:
                if val in true_vals or str(val).lower() in true_vals:
                    queries.append(queryset.filter(promotion__isnull=False, promotion__gt=0))
                elif val in false_vals or str(val).lower() in false_vals:
                    queries.append(queryset.filter(promotion__isnull=True) | queryset.filter(promotion__lte=0))
            if queries:
                result = queries[0]
                for q in queries[1:]:
                    result = result.union(q)
                return result

        if value in true_vals or str(value).lower() in true_vals:
            return queryset.filter(promotion__isnull=False, promotion__gt=0)
        elif value in false_vals or str(value).lower() in false_vals:
            return queryset.filter(promotion__isnull=True) | queryset.filter(promotion__lte=0)

        return queryset

    def filter_season(self, queryset, name, value):
        if value == "all_season":
            return queryset.filter(season__value="all_season")
        return queryset.filter(season__value=value)

    def filter_sort_by_price(self, queryset, name, value):
        queryset = queryset.annotate(
            final_price=Case(
                When(promotion__isnull=False, then=F("promotion")),
                default=F("price"),
                output_field=DecimalField()
            )
        )

        if value == "cheap":
            return queryset.order_by("final_price")
        elif value == "expensive":
            return queryset.order_by("-final_price")
        return queryset

    def filter_min_price(self, queryset, name, value):
        return queryset.annotate(
            final_price=Case(
                When(promotion__gt=0, then=F("promotion")),
                default=F("price"),
                output_field=DecimalField()
            )
        ).filter(final_price__gte=value)

    def filter_max_price(self, queryset, name, value):
        return queryset.annotate(
            final_price=Case(
                When(promotion__gt=0, then=F("promotion")),
                default=F("price"),
                output_field=DecimalField()
            )
        ).filter(final_price__lte=value)


