
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
# Create your models here.

class Condition(models.Model):
    label = models.CharField(max_length=100, unique=True)  # "Новый"
    value = models.CharField(max_length=100, unique=True)  # "new"

    def __str__(self):
        return self.label

class Manufacturer(models.Model):
    label = models.CharField(max_length=100, unique=True)  # "Michelin"
    value = models.CharField(max_length=100, unique=True)  # "michelin"

    def __str__(self):
        return self.label






class TireType(models.Model):
    label = models.CharField(max_length=100, unique=True)  # "Легковое"
    value = models.CharField(max_length=100, unique=True)  # "passenger"

    def __str__(self):
        return self.label


# ❗️ Сезонность (с label и value)
class Season(models.Model):
    label = models.CharField(max_length=100, unique=True)  # "Зима"
    value = models.CharField(max_length=100, unique=True)  # "winter"

    def __str__(self):
        return self.label


class Product(models.Model):
    FUEL_EFFICIENCY_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
        ('G', 'G'),
    ]

    # ❗️ Сцепление с мокрой дорогой
    WET_GRIP_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
    ]
    title = models.CharField(max_length=100)
    image = CloudinaryField('image')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promotion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    promotion_end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    in_stock = models.IntegerField()
    profile = models.CharField(max_length=50)
    diameter = models.CharField(max_length=100)
    speed_index = models.CharField(max_length=100)
    load_index = models.CharField(max_length=500)
    load_index_for_double = models.CharField(max_length=200)
    is_favorite = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=200)
    model = models.CharField(max_length=255)
    generation = models.CharField(max_length=100)
    modification = models.CharField(max_length=255)
    promotionCategory = models.TextField()
    width = models.CharField(max_length=10)  # "205"
    fuel_efficiency = models.CharField(max_length=1, choices=FUEL_EFFICIENCY_CHOICES)
    wet_grip = models.CharField(max_length=1, choices=WET_GRIP_CHOICES)
    external_noise_level = models.IntegerField()
    condition = models.ForeignKey('Condition',on_delete=models.CASCADE)
    runflat = models.BooleanField(default=False)
    off_road = models.BooleanField(default=False)


    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True)
    tire_type = models.ForeignKey('TireType', on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.title} - {self.id}"





class Category(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
        return self.label

    def get_value(self):
        return self.value  # Возвращает английский текст


class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])  # Рейтинг от 1 до 5
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):
        return f"Comment for {self.product.name} - {self.rating}★"
