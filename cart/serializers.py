from rest_framework import serializers
from .models import *
from product.serializers import *


class ProductSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    image = serializers.SerializerMethodField(help_text="Список изображении")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    price = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['product_Id', 'title', 'price', 'image','in_stock', 'count']

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




    def get_count(self, obj):
        return self.context.get('count', 1)

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = []

    def to_representation(self, instance):
        product = instance.product
        count = instance.count

        unit_price = float(product.promotion) if product.promotion else float(product.price or 0)
        total_price = unit_price * count

        return {
            "product_Id": product.id,
            "title": product.title,
            "price": total_price if not product.negotiable else "Договорная",
            "image": [
                product.image1.url if product.image1 else None,
                product.image2.url if product.image2 else None,
                product.image3.url if product.image3 else None,
                product.image4.url if product.image4 else None,
                product.image5.url if product.image5 else None,
                product.image6.url if product.image6 else None,
                product.image7.url if product.image7 else None,
            ],
            "in_stock": product.in_stock,
            "count": count,
        }

class CartSerializer(serializers.ModelSerializer):
    cart_Id = serializers.IntegerField(source='id', help_text="id карты")
    cart_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['cart_Id',  'total_price', 'subtotal', 'total_quantity', 'ordered', 'cart_items']

    def get_cart_items(self, obj):
        cart_items = obj.cartitem_set.all()
        return CartItemSerializer(cart_items, many=True).data

    def get_total_price(self, obj):
        return sum(
            (item.product.promotion if item.product.promotion else item.product.price) * item.count
            for item in obj.cartitem_set.all()
        )

    def get_subtotal(self, obj):
        total = 0
        for item in obj.cartitem_set.select_related('product').all():
            product = item.product
            if product.promotion is None:
                total += product.price * item.count
        return total

    def get_total_quantity(self, obj):
        return sum(item.count for item in obj.cartitem_set.all())



class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title')
    price = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ['product', 'price', 'count', "product_title"]


    def get_price(self, obj):
        if obj.negotiable:
            return "Договорная"
        return float(obj.price) if obj.price is not None else None




class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)


    class Meta:
        model = Order
        fields = [
            "id", 'user', "first_name", "last_name",
            "email", "phone", "pickup", "delivery",
            "payment_online", "payment_cash", "created_at" , 'items', 'address', 'applications']


        read_only_fields = ("user", "items")

    def validate(self, data):
        """
        Проверяем, что выбрано либо самовывоз, либо доставка, но не оба сразу.
        Также проверяем, что выбрана либо онлайн-оплата, либо наличные.
        """
        if data.get("pickup") and data.get("delivery"):
            raise serializers.ValidationError("Нельзя выбрать и самовывоз, и доставку одновременно.")

        if not data.get("pickup") and not data.get("delivery"):
            raise serializers.ValidationError("Нужно выбрать либо самовывоз, либо доставку.")

        if data.get("payment_online") and data.get("payment_cash"):
            raise serializers.ValidationError("Нельзя выбрать и оплату онлайн, и наличными одновременно.")

        if not data.get("payment_online") and not data.get("payment_cash"):
            raise serializers.ValidationError("Нужно выбрать способ оплаты (онлайн или наличными).")

        return data







