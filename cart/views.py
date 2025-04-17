
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework import status
from django.core.mail import send_mail
from django.db import transaction
from django.conf import settings
from django.utils.timezone import localtime
from rest_framework import generics
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

class CartView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Получить текущую корзину пользователя (неоформленную).",
        responses={200: "Корзина успешно получена", 404: "Корзина не найдена"},
        tags=["Cart"]
    )
    def get(self, request):
        cart = Cart.objects.filter(user=request.user, ordered=False).first()
        if not cart:
            return Response({"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        cart_data = {
            "cart": {
                "cart_Id": cart.id,
                "total_price": sum(
                    (item.product.promotion if item.product.promotion else item.product.price) * item.count
                    for item in cart.cartitem_set.all()
                ),
                "subtotal": sum(item.product.price * item.count for item in cart.cartitem_set.all()),
                "promotion_total": sum(
                    item.product.promotion * item.count
                    for item in cart.cartitem_set.all()
                    if item.product.promotion
                ),
                "total_quantity": sum(item.count for item in cart.cartitem_set.all()),
                "ordered": cart.ordered,
            },
            "cart_items": CartItemSerializer(cart.cartitem_set.all(), many=True).data
        }

        return Response(cart_data)

    @swagger_auto_schema(
        operation_description="Добавление товара в корзину.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product", "count"],
            properties={
                "product": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара"),
                "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество (по умолчанию 1)"),
            },
        ),
        responses={200: "Товар добавлен", 404: "Товар не найден"},
        tags=["Cart"]
    )

    def post(self, request):
        user = request.user
        data = request.data
        cart, _ = Cart.objects.get_or_create(user=user, ordered=False)

        product = get_object_or_404(Product, id=data.get('product'))
        count = int(data.get('count', 1))

        price = product.price * count
        promotion = product.promotion * count if product.promotion else None

        CartItem.objects.create(
            cart=cart,
            user=user,
            product=product,
            count=count,
            price=price
        )

        return Response({'success': 'Item added to your cart'})

    @swagger_auto_schema(
        operation_description="Обновить количество определенного товара в корзине.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product", "count"],
            properties={
                "product": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара"),
                "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Новое количество"),
            },
        ),
        responses={200: "Количество обновлено", 404: "Корзина или товар не найдены"},
        tags=["Cart"]
    )
    def put(self, request):
        user = request.user
        data = request.data

        # Находим корзину пользователя
        cart = get_object_or_404(Cart, user=user, ordered=False)

        # Находим item по корзине и продукту
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=data.get('product'))

        # Обновляем количество
        count = int(data.get('count', cart_item.count))
        cart_item.count = count
        cart_item.save()

        return Response({'success': 'Cart item updated'})

    @swagger_auto_schema(
        operation_description="Удалить товар из корзины.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product"],
            properties={
                "product": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID товара для удаления"),
            },
        ),
        responses={200: "Товар удалён", 404: "Корзина или товар не найдены"},
        tags=["Cart"]
    )


    def delete(self, request):
        user = request.user
        data = request.data
        cart = get_object_or_404(Cart, user=user, ordered=False)

        # Ищем CartItem по товару и корзине
        cart_item = get_object_or_404(CartItem, product_id=data.get('product'), cart=cart)

        cart_item.delete()

        return Response({'success': 'Item removed from cart'})



class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Оформление заказа на основе текущей корзины пользователя. Отправляет письмо администратору и создает заказ с товарами.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["first_name", "last_name", "phone", "email", "address"],
            properties={
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),


                "phone": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Email"),
                "address": openapi.Schema(type=openapi.TYPE_STRING, description="Адрес доставки"),
                "payment_cash": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Оплата наличными"),
                "payment_online": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Оплата онлайн"),
                "pickup": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Самовывоз"),
                "delivery": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Доставка"),
            },
        ),
        responses={
            201: openapi.Response(description="Заказ успешно оформлен"),
            400: "Ошибка валидации / Корзина пуста",
            500: "Ошибка при отправке email"
        },
        tags=["Order"]
    )

    @transaction.atomic
    def post(self, request):
        user = request.user

        # Получаем активную корзину
        cart = get_object_or_404(Cart, user=user, ordered=False)
        cart_items = cart.cartitem_set.select_related('product').all()

        if not cart_items.exists():
            return Response({"error": "Корзина пуста."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Создаем заказ
        order = serializer.save(user=user, cart=cart)

        payment_method = "Оплата картой" if order.payment_online else "Оплата наличными" if order.payment_cash else ""
        delivery_method = "Самовывоз" if order.pickup else "Доставка" if order.delivery else ""

        total_price = 0
        total_quantity = 0
        order_items_text = []
        subtotal = sum(item.product.price * item.count for item in cart_items)
        promotion_total = sum(
            item.product.promotion * item.count
            for item in cart_items
            if item.product.promotion
        )

        for item in cart_items:
            price = item.product.promotion if item.product.promotion else item.product.price
            line_total = price * item.count
            total_price += line_total
            total_quantity += item.count

            order_items_text.append(
                f"Товар: {item.product.title}\n"
                f"Изображение: {item.product.image.url if item.product.image else 'Нет'}\n"
                f"Количество: {item.count}\n"
                f"Цена: {price}c\n"
                f"Общая стоимость: {line_total}c\n"
            )
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=price,
                count=item.count,
            )
        order_date = localtime(order.created_at).strftime("%Y-%m-%d %H:%M")
        # Формируем текст письма
        message = (
            f"📦 Новый заказ №{order.id} (TiresShop)\n\n"
            f"Дата заказа: {order_date}\n\n"
            f"Ф.И.О пользователя: {order.last_name} {order.first_name} \n"
            f"Телефон пользователя: {order.phone}\n"
            f"Email пользователя: {order.email}\n\n"
            f"Способ оплаты: {payment_method}\n"
            f"Способ доставки: {delivery_method}\n"
            f"Адрес: {order.address}\n\n"
            f"Список товаров:\n"
            f"{chr(10).join(order_items_text)}\n"
            f"Итог:\n"
            f"Сумма без учета скидок: {subtotal}c\n"
            f"Итоговая сумма с учетом скидки: {total_price}c\n"
            f"Сумма только со скидкой товаров: {promotion_total}c\n"
            f"Общее количество товаров: {total_quantity} шт.\n"
        )



        try:
            send_mail(
                subject=f"Новый заказ №{order.id}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["tiresshopkg@gmail.com"],
                fail_silently=False,
            )
        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": f"Ошибка при отправке email: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order.total_price = total_price
        order.applications = True  # ✅ Отмечаем как успешно отправленный
        order.save()

        # Завершаем заказ
        cart.ordered = True
        cart.save()
        Cart.objects.create(user=user)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class ApplicationsView(APIView):

    @swagger_auto_schema(
        operation_description="Получение всех успешно оформленных заказов (applications=True). Используется в админке для отслеживания заказов.",
        responses={
            200: openapi.Response(
                description="Список заказов",
                examples={
                    "application/json": [
                        {
                            "id_order": 12,
                            "first_name": "Иван",
                            "last_name": "Иванов",
                            "product": [
                                {
                                    "title": "Nokian Hakkapeliitta",
                                    "total_price": 16000
                                }
                            ]
                        },

                    ]
                }
            )
        },
        tags=["Admin - Orders"]
    )
    def get(self, request):
        orders = Order.objects.filter(applications=True).order_by('-created_at')

        result = []
        for order in orders:
            for item in order.items.all():
                item_total = item.price * item.count
                result.append({
                    'id_order': order.id,
                    'first_name': order.first_name,
                    'last_name': order.last_name,
                    'product': [
                        {
                            'title': item.product.title,
                            'total_price': item_total
                        }
                    ]
                })

        return Response(result)











