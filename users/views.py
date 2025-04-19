from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from django.utils.timezone import localtime
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.core.mail import send_mail
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .serializers import SupportRequestSerializer, UserRegisterSerializer
from rest_framework import status
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from .serializers import SocialLoginSerializer
from .models import User
from .utils import generate_tokens_for_user
import requests
from drf_yasg.utils import swagger_auto_schema
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import generics, status
from drf_yasg.utils import swagger_auto_schema
from datetime import timedelta
from .serializers import LoginSerializer
from .models import User
from .utils import generate_tokens_for_user
from drf_yasg import openapi
from users.serializers import (
    UserRegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserProfileSerializer,
    ChangeForgotPasswordSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ConfirmationCodeSerializer,
    UserSerializer,
    SocialLoginSerializer,
)
from users.models import User, OTP
from config import settings
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from cart.models import OrderItem, Order
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from cart.models import Cart

# Вспомогательная функция для генерации токенов
def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh), str(refresh.access_token)

class TokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт предоставляет возможность пользователю обновить токен доступа (Access Token) с помощью токена обновления (Refresh Token)."
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)



class CustomOrderPagination(LimitOffsetPagination):
    default_limit = 3
    max_limit = None

    def get_paginated_response(self, data):
        return Response({
            'UserMe': data
        })

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю зарегистрироваться и получить токены доступа и обновления."
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh_token, access_token = generate_tokens_for_user(user)

            return Response({
                'user': serializer.data,
                'refresh': refresh_token,
                'access': access_token,
            }, status=status.HTTP_201_CREATED)

        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    MAX_ATTEMPTS = 5  # Максимальное количество попыток
    BLOCK_TIME = 60  # Время блокировки в секундах (60 сек = 1 минута)

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю войти в систему и получить токены доступа и обновления."
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        ip = self.get_client_ip(request)
        cache_key = f"failed_login_{email or ip}"
        block_time_key = f"block_time_{email or ip}"

        # Получаем текущее число неудачных попыток
        attempts = cache.get(cache_key, 0)
        block_end_time = cache.get(block_time_key)

        # Если пользователь уже заблокирован, проверяем оставшееся время
        if block_end_time:
            remaining_time = int((block_end_time - now()).total_seconds())
            if remaining_time > 0:
                return Response(
                    {"error": f"Слишком много неудачных попыток. Попробуйте снова через {remaining_time} секунд."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            else:
                # Сбрасываем блокировку, если время истекло
                cache.delete(cache_key)
                cache.delete(block_time_key)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found!"}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            attempts += 1
            cache.set(cache_key, attempts, timeout=self.BLOCK_TIME)  # Сохраняем количество попыток

            if attempts >= self.MAX_ATTEMPTS:
                block_end_time = now() + timedelta(seconds=self.BLOCK_TIME)
                cache.set(block_time_key, block_end_time, timeout=self.BLOCK_TIME)
                return Response(
                    {"error": f"Вы заблокированы. Попробуйте снова через {self.BLOCK_TIME} секунд."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            raise AuthenticationFailed("Incorrect password!")

        # Если логин успешный, сбрасываем счетчик попыток и время блокировки
        cache.delete(cache_key)
        cache.delete(block_time_key)

        refresh_token, access_token = generate_tokens_for_user(user)

        return Response({
            "refresh": refresh_token,
            "access": access_token,
        })

    def get_client_ip(self, request):
        """Получает IP пользователя"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    pagination_class = CustomOrderPagination

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_summary="Получить текущего пользователя и историю заказов (с кастомной пагинацией)",
        operation_description="""
        Этот эндпоинт возвращает информацию о текущем пользователе и историю его заказов.

        📌 Пагинация:
        - Используется кастомная `LimitOffsetPagination`
        - По умолчанию: `limit=3`
        - Пример: `GET /user/me/?limit=3&offset=3`
        """,
        manual_parameters=[
            openapi.Parameter('limit', openapi.IN_QUERY, description="Сколько заявок вернуть",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('offset', openapi.IN_QUERY, description="Смещение по списку заявок",
                              type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ с обёрткой 'UserMe', содержащей данные пользователя и историю заявок",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "UserMe": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Информация о пользователе",
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                                        "username": openapi.Schema(type=openapi.TYPE_STRING),
                                        "phone": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                "order_history": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    description="История заявок пользователя (максимум 3 заявки на страницу)",
                                    items=openapi.Items(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id_order": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "total_price": openapi.Schema(type=openapi.TYPE_NUMBER,
                                                                          format=openapi.FORMAT_FLOAT),
                                            "date_order": openapi.Schema(type=openapi.TYPE_STRING,
                                                                         format=openapi.FORMAT_DATETIME),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise AuthenticationFailed('Authentication credentials were not provided.')



        user_orders = Order.objects.filter(user=user, applications=True) \
            .prefetch_related('items__product') \
            .order_by('-created_at')

        paginator = self.pagination_class()
        paginated_orders = paginator.paginate_queryset(user_orders, request, view=self)

        history = []

        for order in paginated_orders:
            total_price = 0

            for item in order.items.all():  # Предполагается: order.items -> CartItem
                product = item.product
                price = product.promotion if product.promotion else product.price
                total_price += price * item.count

            history.append({
                "id_order": order.id,
                "total_price": float(total_price),
                "date_order": order.created_at,
            })

        user_data = self.get_serializer(user).data

        response_data = {
            "user": user_data,
            "order_history": history
        }

        return paginator.get_paginated_response(response_data)

class UserApplicationsDetail(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="Получить детали заявки по ID",
        operation_description="Возвращает детальную информацию о заявке данного пользавателя",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "order_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID заявки"),
                    "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME,
                                                 description="Дата создания заказа"),
                    "total_quantity": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                     description="Общее количество всех количеств"),
                    "sub_total": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT,
                                                description="Сумма всех товаров по обычным ценам"),
                    "promotion_total": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT,
                                                      description="Сумма всех товаров, только по акции "),
                    "total_price": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT,
                                                  description="Итоговая сумма заказа"),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        description="Список товаров в заказе",
                        items=openapi.Items(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "product_title": openapi.Schema(type=openapi.TYPE_STRING, description="Название товара"),
                                "price": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT,
                                                        description="Общая цена за товар с учетом акции (price * count)"),
                                "count": openapi.Schema(type=openapi.TYPE_INTEGER,
                                                        description="Количество данного товара в заказе")
                            }
                        )
                    )
                }
            ),
            404: "Order not found",
            401: "Unauthorized"
        }
    )

    def get(self, request, order_id):
        user = request.user

        order = Order.objects.filter(id=order_id, user=user, applications=True).first()
        if not order:
            raise NotFound("Order not found")

        order_items = OrderItem.objects.filter(order=order).select_related('product')

        items_data = []
        total_price = 0
        total_quantity = 0
        sub_total = 0
        promotion_total = 0

        for item in order_items:
            product = item.product
            regular_price = product.price
            has_promo = product.promotion is not None
            promo_price = product.promotion if has_promo else regular_price

            line_sub_total = regular_price * item.count
            line_total = promo_price * item.count

            total_quantity += item.count
            sub_total += line_sub_total
            total_price += line_total

            if has_promo:
                promotion_total += product.promotion * item.count

            items_data.append({
                "product_title": product.title,
                "price": float(line_total),
                "count": item.count
            })

        return Response({
            "order_id": order.id,
            "created_at": order.created_at,

            "total_quantity": total_quantity,
            "sub_total": float(sub_total),
            "promotion_total": float(promotion_total),
            "total_price": float(total_price),
            "items": items_data,

        })

class UserProfileUpdateView(generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю обновить свой профиль."
    )
    def put(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User updated successfully!'}, status=status.HTTP_200_OK)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю выйти из системы."
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh_token"]
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "You have successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Unable to log out."}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю запросить восстановление пароля."
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

            otp_code = OTP.generate_otp()
            OTP.objects.create(user=user, otp=otp_code)

            # Отправляем OTP на email пользователя
            send_mail(
                'Forgot Password OTP',
                f'Your OTP is: {otp_code}',
                settings.EMAIL_HOST_USER,
                [email]
            )

            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmCodeView(generics.GenericAPIView):
    serializer_class = ConfirmationCodeSerializer

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт подтверждает код, отправленный пользователю."
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data.get('code')
        try:
            confirmation_code = OTP.objects.get(otp=code)
        except OTP.DoesNotExist:
            return Response({"error": "Invalid or already confirmed code."}, status=status.HTTP_400_BAD_REQUEST)

        user = confirmation_code.user
        confirmation_code.delete()

        refresh_token, access_token = generate_tokens_for_user(user)

        return Response({
            "message": "Code confirmed successfully.",
            "user_id": str(user.id),
            "refresh": refresh_token,
            "access": access_token,
        })


class ChangeForgotPasswordView(generics.GenericAPIView):
    serializer_class = ChangeForgotPasswordSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю изменить свой пароль."
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['password'])
        user.save()

        return Response({'message': 'The password has been successfully changed.'}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    http_method_names = ['put']

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю сменить пароль."
    )
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['password'])
        user.save()

        return Response({'message': 'The password has been successfully changed.'}, status=status.HTTP_200_OK)



class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = SocialLoginSerializer

    @swagger_auto_schema(
        operation_description="Авторизация через Google с использованием только токена доступа и получение JWT токенов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Токен доступа Google'),
            },
            required=['access_token']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Токены успешно получены",
                examples={
                    "application/json": {
                        "access_token": "google_access_token_example",
                        "refresh_token": "google_refresh_token_example"
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Ошибка аутентификации",
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        # Получаем access_token от фронта
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({"error": "Access token is required!"}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем информацию о пользователе через Google API
        user_info = self.get_google_user_info(access_token)

        # Проверяем, существует ли пользователь в базе
        existing_user = User.objects.filter(email=user_info.get("email")).first()

        if not existing_user:
            # Если пользователь не найден, создаем нового
            new_user = User.objects.create(
                email=user_info.get("email"),
                username=user_info.get("name"),
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name"),
                phone_number=user_info.get("phone_number"),
                profile_picture=user_info.get("picture"),
            )
            user = new_user
        else:
            # Если пользователь найден, обновляем его данные
            existing_user.username = user_info.get("name")
            existing_user.first_name = user_info.get("given_name")
            existing_user.last_name = user_info.get("family_name")
            existing_user.phone_number = user_info.get("phone_number")
            existing_user.profile_picture = user_info.get("picture")
            existing_user.save()
            user = existing_user

        # Генерация токенов
        token = self.get_token(user)
        return Response({'access_token': token['access'], 'refresh_token': token['refresh']})

    def get_google_user_info(self, access_token):
        """
        Используем access_token, чтобы получить данные о пользователе через Google API.
        """
        url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()  # Возвращаем данные о пользователе
        else:
            raise Exception("Unable to fetch user data from Google API")
class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    serializer_class = SocialLoginSerializer

    @swagger_auto_schema(
        operation_description="Авторизация через Facebook и получение JWT токенов.",
        request_body=SocialLoginSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Токены успешно получены",
                examples={
                    "application/json": {
                        "access_token": "facebook_access_token_example",
                        "refresh_token": "facebook_refresh_token_example"
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Ошибка аутентификации",
            ),
        }
    )
    def get_response_data(self):
        user = self.user  # Получаем пользователя
        token = self.get_token(user)  # Получаем JWT токен
        return Response({'access_token': token['access'], 'refresh_token': token['refresh']})

class SupportRequestView(APIView):
    @swagger_auto_schema(
        operation_summary="Отправка жалобы",
        operation_description="Этот эндпоинт принимает жалобы от пользователей и отправляет их на email.",
        request_body=SupportRequestSerializer,
        responses={
            200: openapi.Response(
                description="Ваша жалоба успешно отправлена!",
                examples={
                    'application/json': {
                        "message": "Ваша жалоба успешно отправлена!",
                        "created_at": "2025-04-04 14:23:01"  # Пример форматированной даты
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка валидации данных",
                examples={
                    'application/json': {
                        "message": "Ошибка валидации данных"
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = SupportRequestSerializer(data=request.data)
        if serializer.is_valid():
            support_request = serializer.save()  # Сохранение в БД

            name = support_request.name
            phone = support_request.phone
            email = support_request.email
            message = support_request.message
            created_at = localtime(support_request.created_at).strftime("%Y-%m-%d %H:%M:%S")  # Форматируем дату

            subject = f"🚗 TiresShop | Получена новая жалоба..."
            body = f"""
            🛒 *Магазин:* TiresShop
            👤 *Имя:* {name}
            📞 *Телефон:* {phone}
            ✉️ *Email:* {email}
            ⌛ *Время:* {created_at}
            💬 *Сообщение:* 

            {message}
            ───────────────────
            """

            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,  # Используем EMAIL_HOST_USER вместо DEFAULT_FROM_EMAIL
                ["tiresshopkg@gmail.com"],
                fail_silently=False,
            )

            return Response(
                {"message": "Ваша жалоба успешно отправлена!", "created_at": created_at},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

