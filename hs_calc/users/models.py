import django.conf
import django.contrib.auth.models as auth_models
import django.db.models
import phonenumber_field.modelfields


class CustomUser(auth_models.AbstractUser):
    email = django.db.models.EmailField(
        verbose_name="почта",
        unique=True,
    )

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class Buyer(django.db.models.Model):
    phone = phonenumber_field.modelfields.PhoneNumberField(
        "телефон",
        unique=True,
        blank=True,
        null=True,
        region="RU",
    )

    email = django.db.models.EmailField(
        verbose_name="почта",
        unique=True,
        blank=True,
        null=True,
    )

    first_name = django.db.models.CharField(
        "Имя",
        max_length=150,
        blank=True,
        null=True,
    )

    last_name = django.db.models.CharField(
        "Фамилия",
        max_length=150,
        blank=True,
        null=True,
    )


class Profile(django.db.models.Model):
    class Role(django.db.models.TextChoices):
        MAIN_MANAGER = "admin", "Администратор"
        GROUP_MANAGER = "dealer", "Дилер"
        WORKER = "carpenter", "Столяр"

    user = django.db.models.OneToOneField(
        django.conf.settings.AUTH_USER_MODEL,
        on_delete=django.db.models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )

    role = django.db.models.CharField(
        "роль",
        max_length=100,
        choices=Role.choices,
        default=Role.GROUP_MANAGER,
    )

    phone = phonenumber_field.modelfields.PhoneNumberField(
        "телефон",
        blank=True,
        null=True,
        region="RU",
    )

    percentage_sale = django.db.models.IntegerField(
        "процент_с_продажи",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "данные_пользователя"
        verbose_name_plural = "данные_пользователей"

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
