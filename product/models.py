
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
# Create your models here.


class Product(models.Model):
    title = models.CharField(max_length=100)
    image = CloudinaryField('image')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promotion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    promotion_end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    in_stock = models.IntegerField()
    seasonality = models.CharField(max_length=100, null=True, blank=True)
    profile = models.CharField(max_length=50, null=True, blank=True)
    diameter = models.CharField(max_length=100)
    speed_index = models.CharField(max_length=100)
    load_indices = models.CharField(max_length=500)
    load_indices_for_double = models.CharField(max_length=200)
    is_favorite = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=200)
    model = models.CharField(max_length=255)
    generation = models.CharField(max_length=100, blank=True, null=True)
    modification = models.CharField(max_length=255, blank=True, null=True)
    body_type = models.CharField(max_length=255, blank=True, null=True)
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
