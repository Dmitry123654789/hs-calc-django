from decimal import Decimal, InvalidOperation
from json import loads

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from calculate.models import ProfitRatio, Scheme
from core.mixins import AdminRequiredMixin


class MarkupView(AdminRequiredMixin, View):
    def get(self, request):
        context = {
            "schemes": Scheme.objects.all().order_by("name"),
            "profit_ratios": ProfitRatio.objects.all().order_by("name"),
        }
        return render(request, "calculate/markup.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        item_type = data.get("type")
        item_id = data.get("id")

        try:
            ratio = Decimal(str(data.get("ratio")))
        except (InvalidOperation, TypeError):
            return JsonResponse(
                {"status": "error", "message": "Некорректное значение коэффициента"},
                status=400,
            )

        model = {"scheme": Scheme, "profit_ratio": ProfitRatio}.get(item_type)
        if model is None:
            return JsonResponse(
                {"status": "error", "message": "Неизвестный тип элемента"},
                status=400,
            )

        updated = model.objects.filter(id=item_id).update(ratio=ratio)
        if not updated:
            raise Http404("Элемент не найден")

        return JsonResponse({"status": "success"})
