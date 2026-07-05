from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    email = models.EmailField(
        verbose_name="почта",
        unique=True,
    )
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class Buyer(models.Model):
    phone = PhoneNumberField(
        verbose_name="телефон",
        unique=True,
        blank=True,
        null=True,
        region="RU",
    )
    email = models.EmailField(
        verbose_name="почта",
        unique=True,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150,
        blank=True,
        null=True,
    )


class Profile(models.Model):
    class Role(models.TextChoices):
        MAIN_MANAGER = "admin", "Администратор"
        GROUP_MANAGER = "dealer", "Дилер"
        WORKER = "carpenter", "Столяр"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )
    role = models.CharField(
        verbose_name="роль",
        max_length=100,
        choices=Role.choices,
        default=Role.GROUP_MANAGER,
    )
    phone = PhoneNumberField(
        verbose_name="телефон",
        blank=True,
        null=True,
        region="RU",
    )
    percentage_sale = models.IntegerField(
        verbose_name="процент с продажи",
        blank=True,
        null=True,
        default=0,
    )

    class Meta:
        verbose_name = "данные пользователя"
        verbose_name_plural = "данные пользователей"

    def __str__(self):
        return self.user.username

    @property
    def is_director(self):
        return self.role == "admin"

    @property
    def is_manager(self):
        return self.role == "dealer"

    @property
    def is_worker(self):
        return self.role == "carpenter"
