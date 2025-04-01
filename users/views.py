from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from rest_framework_simplejwt.authentication import JWTAuthentication

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

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет пользователю войти в систему и получить токены доступа и обновления."
    )
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found!"}, status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password!")

        refresh_token, access_token = generate_tokens_for_user(user)

        return Response({
            "refresh": refresh_token,
            "access": access_token,
        })



class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed('Authentication credentials were not provided.')
        return self.request.user

    @swagger_auto_schema(
        tags=['Authentication'],
        operation_description="Этот эндпоинт позволяет получить информацию о текущем пользователе."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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
        operation_description="Авторизация через Google и получение JWT токенов.",
        request_body=SocialLoginSerializer,
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
    def get_response_data(self):
        user = self.user  # Получаем пользователя
        token = self.get_token(user)  # Получаем JWT токен
        return Response({'access_token': token['access'], 'refresh_token': token['refresh']})


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
