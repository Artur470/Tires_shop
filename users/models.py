from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone
import string
import random

class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        """Создание суперпользователя с обязательными аттрибутами"""
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)

        return self._create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError("You must provide an email")
        return self._create_user(email, password, **other_fields)

    def _create_user(self, email, password, **other_fields):
        """Вспомогательная функция для создания пользователя"""
        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Пользовательская модель с дополнительными полями и настройками"""
    username = models.CharField(max_length=50, unique=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=100, unique=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Использование связей many-to-many для групп и разрешений
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']  # Можно добавить другие обязательные поля

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email}"

    def set_password(self, raw_password):
        """Метод для установки пароля без обязательных символов"""
        super().set_password(raw_password)

    def clean_password(self):
        """Если хотите настроить еще что-то для пароля, но без обязательных символов"""
        pass


class OTP(models.Model):
    """Модель для OTP-кодов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, unique=True)  # Увеличил длину OTP
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_otp():
        """Генерация OTP-кода из цифр и букв"""
        characters = string.digits + string.ascii_uppercase  # Можно добавить буквы
        return ''.join(random.choice(characters) for _ in range(6))  # Увеличил длину OTP

    @property
    def is_expired(self):
        """Проверка, истек ли OTP-код"""
        time_threshold = timezone.now() - timezone.timedelta(minutes=5)
        return self.created_at < time_threshold
