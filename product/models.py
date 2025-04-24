
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
# Create your models here.
from decimal import Decimal
from users.models import User

class Condition(models.Model):
    label = models.CharField(max_length=100, unique=True)  # "Новый"
    value = models.CharField(max_length=100, unique=True)  # "new"

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


class BodyType(models.Model):
    value = models.CharField(max_length=100, unique=True)  # Английское название
    label = models.CharField(max_length=100)  # Русское название

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
    image1 = CloudinaryField('image1')
    image2 = CloudinaryField('image2', null=True, blank=True)
    image3 = CloudinaryField('image3', null=True, blank=True)
    image4 = CloudinaryField('image4', null=True, blank=True)
    image5 = CloudinaryField('image5', null=True, blank=True)
    image6 = CloudinaryField('image6', null=True, blank=True)
    image7 = CloudinaryField('image7', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    negotiable = models.BooleanField(default=False)
    promotion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    promotion_end_date = models.DateTimeField(null=True, blank=True)
    model_description = models.TextField()
    in_stock = models.IntegerField()
    profile = models.CharField(max_length=50)
    diameter = models.CharField(max_length=100)
    speed_index = models.CharField(max_length=100)
    load_index = models.CharField(max_length=500)
    load_index_for_double = models.CharField(max_length=200)
    is_favorite = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=255)
    generation = models.CharField(max_length=100)
    modification = models.CharField(max_length=255)
    promotionCategory = models.TextField(null=True, blank=True)
    width = models.CharField(max_length=10)  # "205"
    fuel_efficiency = models.CharField(max_length=1, choices=FUEL_EFFICIENCY_CHOICES)
    wet_grip = models.CharField(max_length=1, choices=WET_GRIP_CHOICES)
    external_noise_level = models.IntegerField()
    condition = models.ForeignKey('Condition',on_delete=models.CASCADE)
    season = models.ForeignKey('Season', on_delete=models.CASCADE)
    tire_type = models.ForeignKey('TireType', on_delete=models.CASCADE)
    body_type = models.ForeignKey('BodyType', on_delete=models.CASCADE)
    runflat = models.BooleanField(default=False)
    off_road = models.BooleanField(default=False)
    warranty = models.CharField(max_length=100, blank=True, null=True)  # Поле гарантии

    def get_price_display(self):
        return "Договорная" if self.negotiable else f"{self.price} c"


    def __str__(self):
        return f"{self.title} - {self.id}"






class Comment(models.Model):
    RATING_CHOICES = [
        (Decimal("1.0"), "1 ★"),
        (Decimal("1.5"), "1.5 ★"),
        (Decimal("2.0"), "2 ★"),
        (Decimal("2.5"), "2.5 ★"),
        (Decimal("3.0"), "3 ★"),
        (Decimal("3.5"), "3.5 ★"),
        (Decimal("4.0"), "4 ★"),
        (Decimal("4.5"), "4.5 ★"),
        (Decimal("5.0"), "5 ★"),
    ]


    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        choices=RATING_CHOICES,
        validators=[MinValueValidator(Decimal("1.0")), MaxValueValidator(Decimal("5.0"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment for {self.product.name} - {self.rating}★"




class News(models.Model):
    news_image = CloudinaryField('image')
    news_title = models.CharField(max_length=255)
    news_time = models.DateTimeField(auto_now_add=True)
    news_description = models.TextField()


    def __str__(self):
        return self.news_title




