import django.db.models

import users.models


class Order(django.db.models.Model):
    delivery = django.db.models.PositiveIntegerField(
        default=False,
        verbose_name="Доставка",
    )
    installation = django.db.models.PositiveIntegerField(
        default=False,
        verbose_name="Монтаж",
    )
    unloading = django.db.models.PositiveIntegerField(
        default=False,
        verbose_name="Разгрузка",
    )
    discount = django.db.models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Скидка",
    )
    dealer = django.db.models.ForeignKey(
        users.models.CustomUser,
        on_delete=django.db.models.CASCADE,
    )
    buyer = django.db.models.ForeignKey(
        users.models.Buyer,
        on_delete=django.db.models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = django.db.models.DateTimeField(auto_now_add=True)
