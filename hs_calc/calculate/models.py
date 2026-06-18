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

import orders.models


class Scheme(Model):
    name = CharField(
        max_length=100,
        verbose_name="Название схемы",
    )
    min_size = PositiveIntegerField(
        verbose_name="Мин. размер (мм)",
    )
    max_size = PositiveIntegerField(
        verbose_name="Макс. размер (мм)",
    )
    door = PositiveIntegerField()
    fixed_sash = PositiveIntegerField()
    rail_amour = PositiveIntegerField()
    door_sub = PositiveIntegerField()
    sash_sub = PositiveIntegerField()

    def __str__(self):
        return self.name


class BaseMaterial(Model):
    name = CharField(max_length=50)
    price = PositiveIntegerField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Glass(BaseMaterial):
    pass


class Beams(BaseMaterial):
    length = PositiveIntegerField()
    identity = CharField(max_length=50)


class GlukharWood(BaseMaterial):
    length = PositiveIntegerField()

    class Meta:
        db_table = "calculate_glukhar_wood"


class Hardware(BaseMaterial):
    length = PositiveIntegerField()


class GlukharGlass(BaseMaterial):
    min_area = PositiveIntegerField()
    max_area = PositiveIntegerField()

    class Meta:
        db_table = "calculate_glukhar_glass"


class Color(BaseMaterial):
    coverage_rate_doors = DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    coverage_rate_sash = DecimalField(
        max_digits=10,
        decimal_places=2,
    )


class PortalWood(Model):
    name = CharField(
        max_length=50,
    )

    ratio = DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_portal_wood"


class ProfitRatio(Model):
    name = CharField(
        max_length=50,
    )
    ratio = DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_profit_ratio"


class Work(Model):
    beam = CharField(max_length=50)
    carpenter = DecimalField(max_digits=10, decimal_places=2)
    painter = DecimalField(max_digits=10, decimal_places=2)


class BaseProduct(Model):
    width = PositiveIntegerField(verbose_name="Ширина")
    height = PositiveIntegerField(verbose_name="Высота")

    color_type = ForeignKey(
        Color,
        on_delete=PROTECT,
    )
    is_finished = BooleanField(
        default=False,
    )
    order = ForeignKey(
        orders.models.Order,
        on_delete=PROTECT,
    )
    amount = PositiveIntegerField(verbose_name="Количество")

    calculation_details = JSONField(blank=True)

    class Meta:
        abstract = True


class Portal(BaseProduct):
    class Color(TextChoices):
        Silver = "silver", "Серебро"
        Бронза = "bronze", "Бронза"
        White = "white", "Белый"
        Brown = "brown", "Коричневый"

    glass = ForeignKey(
        Glass,
        on_delete=PROTECT,
    )
    wood_type = ForeignKey(
        PortalWood,
        on_delete=PROTECT,
    )
    scheme = ForeignKey(
        Scheme,
        on_delete=PROTECT,
    )
    hardware_type = ForeignKey(
        Hardware,
        on_delete=PROTECT,
    )
    hardware_color = CharField(
        max_length=100,
        choices=Color.choices,
        default=Color.White,
    )
    has_rain_protection = BooleanField(
        default=False,
        verbose_name="Есть_ли_дождь",
    )


class Glukhar(BaseProduct):
    is_non_rectangular = BooleanField(
        default=False,
        verbose_name="Не_прямоугольник",
    )
    wood_type = ForeignKey(
        GlukharWood,
        on_delete=PROTECT,
    )
