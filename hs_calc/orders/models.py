from django.db.models import (
    CASCADE,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    PositiveIntegerField,
    SET_NULL,
)

import users.models


class Order(Model):
    delivery = PositiveIntegerField(
        default=False,
        verbose_name="Доставка",
    )
    installation = PositiveIntegerField(
        default=False,
        verbose_name="Монтаж",
    )
    unloading = PositiveIntegerField(
        default=False,
        verbose_name="Разгрузка",
    )
    discount = DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Скидка",
    )
    dealer = ForeignKey(
        users.models.CustomUser,
        on_delete=CASCADE,
    )
    buyer = ForeignKey(
        users.models.Buyer,
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )
    created_at = DateTimeField(auto_now_add=True)
