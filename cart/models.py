from django.db import models
from users.models import User
from product.models import Product


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.FloatField(default=0)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.username) + " " + str(self.total_price)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    IsOrder = models.BooleanField(default=False)
    count = models.IntegerField(default=1)

    def __str__(self):
        return str(self.cart.user.username) + " " + str(self.cart.total_price)


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")

    email = models.EmailField(verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    pickup = models.BooleanField(default=False)  # Самовывоз
    delivery = models.BooleanField(default=False)  # Доставка
    address = models.TextField()

    # Способы оплаты
    payment_online = models.BooleanField(default=False)  # Онлайн-оплата
    payment_cash = models.BooleanField(default=False)  # Наличные

    applications = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заказ #{self.pk} от {self.last_name} {self.first_name} "

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    count = models.IntegerField()
    negotiable = models.BooleanField(default=False)

    def get_price_display(self):
        return "Договорная" if self.negotiable else f"{self.price} c"

    def __str__(self):
        return f"{self.product.title} x {self.count}"



