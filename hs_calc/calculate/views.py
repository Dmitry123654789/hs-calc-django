from decimal import Decimal, InvalidOperation
from json import loads

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from calculate.models import FixedExpenses, ProfitRatio, Scheme
from core.mixins import AdminRequiredMixin


PROFIT_CALC_NAMES = ("acquiring",)
REWARD_CALC_NAMES = ("money_transfer", "revenue")

RATIO_LABELS = {
    "glukhar": "Глухари",
    "acquiring": "Эквайринг и налоги",
    "money_transfer": "Комиссия за перевод",
    "revenue": "Налог с выручки",
}
FIXED_EXPENSES_LABELS = {
    "monthly_efficiency": "Постоянные расходы/месяц, руб",
    "monthly_expenses": "Производительность, м²/месяц",
}

TYPE_CONFIG = {
    "scheme": (Scheme, "ratio", Decimal),
    "profit_ratio": (ProfitRatio, "ratio", Decimal),
    "fixed_expenses": (FixedExpenses, "price", int),
}


class MarkupView(AdminRequiredMixin, View):
    def get(self, request):
        special_names = PROFIT_CALC_NAMES + REWARD_CALC_NAMES

        context = {
            "schemes": Scheme.objects.all().order_by("name"),
            "profit_ratios": ProfitRatio.objects.exclude(name__in=special_names).order_by(
                "name",
            ),
            "profit_calc_ratios": ProfitRatio.objects.filter(
                name__in=PROFIT_CALC_NAMES,
            ).order_by("name"),
            "reward_calc_ratios": ProfitRatio.objects.filter(
                name__in=REWARD_CALC_NAMES,
            ).order_by("name"),
            "ratio_labels": RATIO_LABELS,
            "fixed_expenses": FixedExpenses.objects.all().order_by("name"),
            "fixed_expenses_labels": FIXED_EXPENSES_LABELS,
        }
        return render(request, "calculate/markup.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        item_type = data.get("type")
        item_id = data.get("id")

        config = TYPE_CONFIG.get(item_type)
        if config is None:
            return JsonResponse(
                {"status": "error", "message": "Неизвестный тип элемента"},
                status=400,
            )

        model, field_name, caster = config
        raw_value = data.get("value", data.get("ratio"))

        try:
            value = caster(raw_value) if caster is int else Decimal(str(raw_value))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse(
                {"status": "error", "message": "Некорректное значение"},
                status=400,
            )

        if value < 0:
            return JsonResponse(
                {"status": "error", "message": "Значение не может быть отрицательным"},
                status=400,
            )

        updated = model.objects.filter(id=item_id).update(**{field_name: value})
        if not updated:
            raise Http404("Элемент не найден")

        return JsonResponse({"status": "success"})
