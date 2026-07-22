from django.db.models import (
    BooleanField,
    CASCADE,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    PositiveIntegerField,
    SET_NULL,
)

from users.models import Buyer, CustomUser


class Order(Model):
    delivery = PositiveIntegerField(
        verbose_name="Доставка",
    )
    installation = PositiveIntegerField(
        verbose_name="Монтаж",
        default=False,
    )
    unloading = PositiveIntegerField(
        verbose_name="Разгрузка",
        default=False,
    )
    discount = DecimalField(
        verbose_name="Скидка",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    creator = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        verbose_name="Создатель",
    )
    buyer = ForeignKey(
        Buyer,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        verbose_name="Покупатель",
    )
    is_finished = BooleanField(
        verbose_name="Завершен",
        default=False,
    )
    created_at = DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )
    percentage_worker = DecimalField(
        verbose_name="процент работника",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total_sum = DecimalField(
        verbose_name="стоимость всего заказа",
        max_digits=11,
        decimal_places=2,
        default=0,
    )
