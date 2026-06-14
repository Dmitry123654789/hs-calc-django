import django.db.models

import orders.models


class Scheme(django.db.models.Model):
    name = django.db.models.CharField(
        max_length=100,
        verbose_name="Название схемы",
    )
    min_size = django.db.models.PositiveIntegerField(
        verbose_name="Мин. размер (мм)",
    )
    max_size = django.db.models.PositiveIntegerField(
        verbose_name="Макс. размер (мм)",
    )
    door = django.db.models.PositiveIntegerField()
    fixed_sash = django.db.models.PositiveIntegerField()
    rail_amour = django.db.models.PositiveIntegerField()
    door_sub = django.db.models.PositiveIntegerField()
    sash_sub = django.db.models.PositiveIntegerField()

    def __str__(self):
        return self.name


class BaseMaterial(django.db.models.Model):
    name = django.db.models.CharField(max_length=50)
    price = django.db.models.PositiveIntegerField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Glass(BaseMaterial):
    pass


class Beams(BaseMaterial):
    length = django.db.models.PositiveIntegerField()
    identity = django.db.models.CharField(max_length=50)


class GlukharWood(BaseMaterial):
    length = django.db.models.PositiveIntegerField()

    class Meta:
        db_table = "calculate_glukhar_wood"


class Hardware(BaseMaterial):
    length = django.db.models.PositiveIntegerField()


class GlukharGlass(BaseMaterial):
    min_area = django.db.models.PositiveIntegerField()
    max_area = django.db.models.PositiveIntegerField()

    class Meta:
        db_table = "calculate_glukhar_glass"


class Color(BaseMaterial):
    coverage_rate_doors = django.db.models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    coverage_rate_sash = django.db.models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


class PortalWood(django.db.models.Model):
    name = django.db.models.CharField(
        max_length=50,
    )

    ratio = django.db.models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_portal_wood"


class ProfitRatio(django.db.models.Model):
    name = django.db.models.CharField(
        max_length=50,
    )
    ratio = django.db.models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    class Meta:
        db_table = "calculate_profit_ratio"


class Work(django.db.models.Model):
    beam = django.db.models.CharField(max_length=50)
    carpenter = django.db.models.DecimalField(max_digits=10, decimal_places=2)
    painter = django.db.models.DecimalField(max_digits=10, decimal_places=2)


class BaseProduct(django.db.models.Model):
    width = django.db.models.PositiveIntegerField(verbose_name="Ширина")
    height = django.db.models.PositiveIntegerField(verbose_name="Высота")

    color_type = django.db.models.ForeignKey(
        Color,
        on_delete=django.db.models.PROTECT,
    )
    is_finished = django.db.models.BooleanField(
        default=False,
    )
    order = django.db.models.ForeignKey(
        orders.models.Order,
        on_delete=django.db.models.PROTECT,
    )
    amount = django.db.models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        abstract = True


class Portal(BaseProduct):
    class Color(django.db.models.TextChoices):
        Silver = "silver", "Серебро"
        Бронза = "bronze", "Бронза"
        White = "white", "Белый"
        Brown = "brown", "Коричневый"

    glass = django.db.models.ForeignKey(
        Glass,
        on_delete=django.db.models.PROTECT,
    )
    wood_type = django.db.models.ForeignKey(
        PortalWood,
        on_delete=django.db.models.PROTECT,
    )
    scheme = django.db.models.ForeignKey(
        Scheme,
        on_delete=django.db.models.PROTECT,
    )
    hardware_type = django.db.models.ForeignKey(
        Hardware,
        on_delete=django.db.models.PROTECT,
    )
    hardware_color = django.db.models.CharField(
        max_length=100,
        choices=Color.choices,
        default=Color.White,
    )
    has_rain_protection = django.db.models.BooleanField(
        default=False,
        verbose_name="Есть_ли_дождь",
    )


class Glukhar(BaseProduct):
    is_non_rectangular = django.db.models.BooleanField(
        default=False,
        verbose_name="Не_прямоугольник",
    )
    wood_type = django.db.models.ForeignKey(
        GlukharWood,
        on_delete=django.db.models.PROTECT,
    )
