from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Model,
    PositiveIntegerField,
    SET_NULL,
    TextChoices,
)

from users.models import Buyer, CustomUser


class Order(Model):
    class Status(TextChoices):
        Ordered = "ordered", "Заказано"
        In_work = "in_work", "В работе"
        Done = "done", "Выполнено"
        Cancelled = "cancelled", "Отменено"

    delivery = PositiveIntegerField(
        verbose_name="Доставка",
    )
    installation = PositiveIntegerField(
        verbose_name="Монтаж",
        default=0,
    )
    installation_cost = DecimalField(
        verbose_name="Стоимость монтажа",
        max_digits=11,
        decimal_places=2,
        default=0,
    )
    unloading = PositiveIntegerField(
        verbose_name="Разгрузка",
        default=0,
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
    status = CharField(
        verbose_name="Цвет фурнитуры",
        max_length=100,
        choices=Status.choices,
        default=Status.Ordered,
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
    profit = DecimalField(
        verbose_name="Прибыль",
        max_digits=11,
        decimal_places=2,
        default=0,
    )
