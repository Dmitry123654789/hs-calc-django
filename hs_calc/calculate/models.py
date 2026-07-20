from django.db.models import (
    BooleanField,
    CharField,
    DecimalField,
    ForeignKey,
    JSONField,
    Model,
    PositiveIntegerField,
    PROTECT,
    TextChoices,
)

from orders.models import Order


class Scheme(Model):
    name = CharField(
        verbose_name="Название схемы",
        max_length=100,
    )
    min_size = PositiveIntegerField(
        verbose_name="Мин. размер (мм)",
    )
    max_size = PositiveIntegerField(
        verbose_name="Макс. размер (мм)",
    )
    door = PositiveIntegerField(
        verbose_name="Дверь",
    )
    fixed_sash = PositiveIntegerField(
        verbose_name="Фиксированная створка",
    )
    rail_amour = PositiveIntegerField(
        verbose_name="Рейка арматура",
    )
    door_sub = PositiveIntegerField(
        verbose_name="Дверной подстав",
    )
    sash_sub = PositiveIntegerField(
        verbose_name="Створочный подстав",
    )
    ratio = DecimalField(
        verbose_name="Коэффициент прибыли",
        max_digits=5,
        decimal_places=2,
    )

    def __str__(self):
        return self.name


class BaseMaterial(Model):
    name = CharField(
        verbose_name="Название",
        max_length=50,
    )
    price = PositiveIntegerField(
        verbose_name="Цена",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Glass(BaseMaterial):
    pass


class Beams(BaseMaterial):
    length = PositiveIntegerField(
        verbose_name="Длина",
    )
    identity = CharField(
        verbose_name="Идентификатор",
        max_length=50,
    )


class GlukharWood(BaseMaterial):
    length = PositiveIntegerField(
        verbose_name="Длина",
    )

    class Meta:
        db_table = "calculate_glukhar_wood"


class Hardware(BaseMaterial):
    length = PositiveIntegerField(
        verbose_name="Длина",
    )


class GlukharGlass(BaseMaterial):
    min_area = PositiveIntegerField(
        verbose_name="Мин. площадь",
    )
    max_area = PositiveIntegerField(
        verbose_name="Макс. площадь",
    )

    class Meta:
        db_table = "calculate_glukhar_glass"


class Color(BaseMaterial):
    coverage_rate_doors = DecimalField(
        verbose_name="Норма расхода на двери",
        max_digits=10,
        decimal_places=2,
    )
    coverage_rate_sash = DecimalField(
        verbose_name="Норма расхода на створки",
        max_digits=10,
        decimal_places=2,
    )


class PortalWood(Model):
    name = CharField(
        verbose_name="Название",
        max_length=50,
    )
    ratio = DecimalField(
        verbose_name="Коэффициент",
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_portal_wood"

    def __str__(self):
        return self.name.capitalize()


class ProfitRatio(Model):
    name = CharField(
        verbose_name="Название",
        max_length=50,
    )
    ratio = DecimalField(
        verbose_name="Коэффициент прибыли",
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_profit_ratio"


class Work(Model):
    beam = CharField(
        verbose_name="Брус",
        max_length=50,
    )
    carpenter = DecimalField(
        verbose_name="Столяр",
        max_digits=10,
        decimal_places=2,
    )
    painter = DecimalField(
        verbose_name="Маляр",
        max_digits=10,
        decimal_places=2,
    )


class BaseProduct(Model):
    width = PositiveIntegerField(
        verbose_name="Ширина",
    )
    height = PositiveIntegerField(
        verbose_name="Высота",
    )
    color_type = ForeignKey(
        Color,
        on_delete=PROTECT,
        verbose_name="Тип цвета",
    )
    is_finished = BooleanField(
        verbose_name="Готово",
        default=False,
    )
    order = ForeignKey(
        Order,
        on_delete=PROTECT,
        verbose_name="Заказ",
    )
    amount = PositiveIntegerField(
        verbose_name="Количество",
    )
    calculation_details = JSONField(
        verbose_name="Детали расчета",
        blank=True,
    )

    class Meta:
        abstract = True


class Portal(BaseProduct):
    class Color(TextChoices):
        Silver = "silver ", "Серебро "
        Бронза = "bronze ", "Бронза "
        White = "white ", "Белый "
        Brown = "brown ", "Коричневый "

    glass = ForeignKey(
        Glass,
        on_delete=PROTECT,
        verbose_name="Стекло",
    )
    wood_type = ForeignKey(
        PortalWood,
        on_delete=PROTECT,
        verbose_name="Тип дерева",
    )
    scheme = ForeignKey(
        Scheme,
        on_delete=PROTECT,
        verbose_name="Схема",
    )
    hardware_type = ForeignKey(
        Hardware,
        on_delete=PROTECT,
        verbose_name="Тип фурнитуры",
    )
    hardware_color = CharField(
        verbose_name="Цвет фурнитуры",
        max_length=100,
        choices=Color.choices,
        default=Color.White,
    )
    has_rain_protection = BooleanField(
        verbose_name="Есть ли защита от дождя",
        default=False,
    )


class Glukhar(BaseProduct):
    is_non_rectangular = BooleanField(
        verbose_name="Не прямоугольник",
        default=False,
    )
    wood_type = ForeignKey(
        GlukharWood,
        on_delete=PROTECT,
        verbose_name="Тип дерева",
    )
