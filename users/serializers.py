from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from users.models import User, OTP
import re


class PasswordMixin(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # Проверка на совпадение паролей
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"error": "Пароли не совпадают."})

        password = attrs['password']

        # Проверка на наличие хотя бы одной заглавной буквы
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({'password': "Пароль должен содержать хотя бы одну заглавную букву."})

        # Специальные символы теперь не обязательны
        # Убираем обязательность наличия хотя бы одного специального символа
        # if not re.search(r'[!@#$%^&*]', password):
        #     raise serializers.ValidationError(
        #         {'password': "Пароль должен содержать хотя бы один специальный символ (!@#$%^&*)."}
        #     )

        # Проверка на минимальную длину пароля
        if len(password) < 8:
            raise serializers.ValidationError({'password': "Пароль должен быть не короче 8 символов."})

        return attrs


class UserRegisterSerializer(serializers.ModelSerializer, PasswordMixin):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'phone',
            'password',
            'confirm_password',
        ]

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Пароль'}
    )

    class Meta:
        model = User
        fields = ["email", "password"]


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ["username", "email"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже используется.")
        return value

    def update(self, instance, validated_data):
        # Обновляем поля пользователя, если они предоставлены
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)

        # Сохраняем объект
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    """ Используется для получения информации о пользователе (без паролей) """

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'phone',
        ]


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmationCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=4)

    def validate(self, data):
        code = data.get('code')

        try:
            otp_obj = OTP.objects.get(otp=code)
            if otp_obj.is_expired:
                raise serializers.ValidationError({'error': "OTP-код истек."})
        except OTP.DoesNotExist:
            raise serializers.ValidationError({'error': "Неверный OTP-код."})

        return data


class ChangeForgotPasswordSerializer(serializers.ModelSerializer, PasswordMixin):
    class Meta:
        model = User
        fields = ['password', 'confirm_password']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not check_password(value, user.password):
            raise serializers.ValidationError({"error": "Неверный старый пароль."})
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"error": "Пароли не совпадают."})
        return attrs

    class Meta:
        model = User
        fields = ['old_password', 'password', 'confirm_password']


class SocialLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(
        help_text="Токен доступа, полученный от социальной сети. Используется для аутентификации в приложении."
    )
    code = serializers.CharField(
        help_text="Код, полученный после успешной аутентификации через социальную сеть."
    )
    id_token = serializers.CharField(
        help_text="Идентификатор пользователя, полученный через социальную сеть. Используется для получения информации о пользователе."
    )
