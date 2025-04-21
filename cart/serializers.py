from rest_framework import serializers
from .models import *
from product.serializers import *


class ProductSerializer(serializers.ModelSerializer):
    product_Id = serializers.IntegerField(source='id', help_text="id товара")
    image1 = serializers.SerializerMethodField(help_text="изображение шин #1")
    image2 = serializers.SerializerMethodField(help_text="изображение шин #2")
    image3 = serializers.SerializerMethodField(help_text="изображение шин #3")
    image4 = serializers.SerializerMethodField(help_text="изображение шин #4")
    image5 = serializers.SerializerMethodField(help_text="изображение шин #5")
    image6 = serializers.SerializerMethodField(help_text="изображение шин #6")
    image7 = serializers.SerializerMethodField(help_text="изображение шин #7")
    in_stock = serializers.IntegerField(help_text="количество шины в складе")
    price = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['product_Id', 'title', 'price', 'image1', 'image2', 'image3', 'image4', 'image5', 'image6', 'image7', 'in_stock', 'count']

    def get_image1(self, obj):
        if obj.image1:
            return obj.image1.url
        return None

    def get_image2(self, obj):
        if obj.image2:
            return obj.image2.url
        return None

    def get_image3(self, obj):
        if obj.image3:
            return obj.image3.url
        return None

    def get_image4(self, obj):
        if obj.image4:
            return obj.image4.url
        return None

    def get_image5(self, obj):
        if obj.image5:
            return obj.image5.url
        return None

    def get_image6(self, obj):
        if obj.image6:
            return obj.image6.url
        return None

    def get_image7(self, obj):
        if obj.image7:
            return obj.image7.url
        return None


    def get_price(self, obj):
        count = self.context.get('count', 1)
        unit_price = obj.promotion if obj.promotion else obj.price
        return unit_price * count

    def get_count(self, obj):
        return self.context.get('count', 1)

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()



    class Meta:
        model = CartItem
        fields = ['product']

    def get_product(self, obj):
        return ProductSerializer(obj.product, context={'count': obj.count}).data

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
    class Meta:
        model = OrderItem
        fields = ['product', 'price', 'count', "product_title"]




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







