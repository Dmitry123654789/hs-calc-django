import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from calculate.forms import CalculationForm
from calculate.models import (
    Color,
    Glass,
    Glukhar,
    GlukharWood,
    Hardware,
    Portal,
    PortalWood,
    ProfitRatio,
    Scheme,
)
from calculate.services import calculate_beams, calculate_glukhar
from orders.models import Order
from users.models import Buyer


class GlukharOrderView(LoginRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="glukhar")
        profit_ratio = float(ratio_obj.ratio)

        return render(request, "calculate/glukhar.html", {"profit_ratio": profit_ratio})

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        try:
            result = calculate_glukhar(data)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse(
                {"error": f"Внутренняя ошибка расчета: {str(e)}"},
                status=500,
            )


class SaveGlukharOrderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        buyer_id = data.get("buyer_id")
        buyer_data = data.get("buyer_data")

        installation = int(data.get("installation"))
        delivery = int(data.get("delivery"))
        unloading = int(data.get("unloading"))
        discount = int(data.get("discount", 0))

        material_name = data.get("material")
        color_name = data.get("color")
        wood_type = GlukharWood.objects.get(name=material_name)
        color_type = Color.objects.get(name=color_name)

        buyer = None
        if buyer_id not in ["null", "new"]:
            buyer = Buyer.objects.get(id=buyer_id)
        elif buyer_id == "new":
            clean_data = {k: (v if v else None) for k, v in buyer_data.items()}
            with transaction.atomic():
                buyer = Buyer.objects.create(**clean_data)

        with transaction.atomic():
            order = Order.objects.create(
                delivery=delivery,
                installation=installation,
                unloading=unloading,
                discount=discount,
                dealer=request.user,
                buyer=buyer,
            )

        with transaction.atomic():
            for key, value in data.items():
                if key.startswith("glukhar"):
                    width = value.get("width")
                    height = value.get("height")
                    amount = value.get("amount")
                    is_not_rect = value.get("is_not_rectangle", False)

                    Glukhar.objects.create(
                        width=int(width),
                        height=int(height),
                        wood_type=wood_type,
                        color_type=color_type,
                        is_non_rectangular=is_not_rect,
                        order=order,
                        amount=amount,
                    )

        return JsonResponse({"status": "success"})


class PortalOrderView(LoginRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="portal")

        schemes = list(Scheme.objects.values("id", "name", "min_size", "max_size"))
        context = {
            "profit_ratio": float(ratio_obj.ratio),
            "schemes_json": json.dumps(schemes),
        }
        return render(request, "calculate/portal_order.html", context)


class PortalOrderCalculateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        portals = payload.get("portals", [])
        total_price = 0
        results_data = []

        for index, portal in enumerate(portals):
            data, labor_data = calculate_beams(
                portal_width=portal["width"],
                portal_height=portal["height"],
                has_rain=portal["has_rain"],
                hardware=portal["hardware"],
                color=portal["color"],
                glass_type=portal["glazing"],
                schemes=[portal["scheme"]],
                wood_type=portal["wood_type"],
            )

            portal_total = 0

            for s_data in data.values():
                for detail_data in s_data.values():
                    portal_total += detail_data["price"]

            portal_total *= portal["amount"]
            total_price += portal_total

            results_data.append(
                {
                    "id": index + 1,
                    "amount": portal["amount"],
                    "width": portal["width"],
                    "height": portal["height"],
                    "scheme": portal["scheme"],
                    "wood_type": portal["wood_type"],
                    "color": portal["color"],
                    "hardware": portal["hardware"],
                    "glazing": portal["glazing"],
                    "has_rain": portal["has_rain"],
                    "portal_total": portal_total,
                },
            )

        try:
            ratio_obj = ProfitRatio.objects.get(name="portal")
            profit_ratio = float(ratio_obj.ratio)
        except (ProfitRatio.DoesNotExist, ValueError):
            profit_ratio = 1.0

        return JsonResponse(
            {
                "status": "success",
                "results": results_data,
                "total_portals_price": total_price,
                "profit_ratio": profit_ratio,
            },
        )


class PortalOrderSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        buyer_id = data.get("buyer_id")
        buyer_data = data.get("buyer_data")

        installation = int(data.get("installation"))
        delivery = int(data.get("delivery"))
        unloading = int(data.get("unloading"))
        discount = int(data.get("discount", 0))

        buyer = None
        if buyer_id not in ["null", "new"]:
            buyer = Buyer.objects.get(id=buyer_id)
        elif buyer_id == "new":
            clean_data = {k: (v if v else None) for k, v in buyer_data.items()}
            with transaction.atomic():
                buyer = Buyer.objects.create(**clean_data)

        with transaction.atomic():
            order = Order.objects.create(
                delivery=delivery,
                installation=installation,
                unloading=unloading,
                discount=discount,
                dealer=request.user,
                buyer=buyer,
            )

        portals = data.get("portals", [])
        with transaction.atomic():
            for p in portals:
                width = int(p.get("width"))
                height = int(p.get("height"))
                has_rain = bool(p.get("has_rain", False))
                scheme_obj = Scheme.objects.get(name=p.get("scheme"))
                wood_obj = PortalWood.objects.get(name=p.get("wood_type").lower())
                hardware_obj = Hardware.objects.get(name=p.get("hardware"))
                glass_obj = Glass.objects.get(name=p.get("glazing"))
                hardware_color = p.get("hardware_color")
                color_type = Color.objects.get(name=p.get("color"))
                amount = int(p.get("amount"))

                Portal.objects.create(
                    width=width,
                    height=height,
                    has_rain_protection=has_rain,
                    color_type=color_type,
                    hardware_type=hardware_obj,
                    scheme=scheme_obj,
                    wood_type=wood_obj,
                    hardware_color=hardware_color,
                    glass=glass_obj,
                    order=order,
                    amount=amount,
                )

        return JsonResponse({"status": "success"})


class PortalAdminView(LoginRequiredMixin, FormView):
    template_name = "calculate/portal_admin.html"
    form_class = CalculationForm
    success_url = reverse_lazy("calculate:result")

    def form_valid(self, form):
        self.request.session["portal_width"] = form.cleaned_data["width"]
        self.request.session["portal_height"] = form.cleaned_data["height"]
        self.request.session["has_rain"] = form.cleaned_data["has_rain"]
        self.request.session["color"] = form.cleaned_data["color"]
        self.request.session["hardware"] = form.cleaned_data["hardware"]
        self.request.session["glazing"] = form.cleaned_data["glazing"]
        self.request.session["wood_type"] = form.cleaned_data["wood_type"]

        schemes_str = form.cleaned_data.get("scheme", "")
        self.request.session["schemes"] = [
            s.strip() for s in schemes_str.split(",") if s.strip()
        ]

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" in context and hasattr(context["form"], "schemes_data"):
            context["schemes"] = context["form"].schemes_data
        else:
            context["schemes"] = Scheme.objects.values(
                "id",
                "name",
                "min_size",
                "max_size",
            )

        return context

    def get(self, request, *args, **kwargs):
        width = request.GET.get("width")
        schemes = Scheme.objects.all()
        print(width)
        if width:
            width = int(width)
            schemes = schemes.filter(min_size__lte=width, max_size__gte=width)

        data = [
            {
                "name": s.name,
                "min_size": s.min_size,
                "max_size": s.max_size,
            }
            for s in schemes
        ]

        return JsonResponse(data, safe=False)


class ResultView(LoginRequiredMixin, TemplateView):
    template_name = "calculate/result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.request.session

        # Старый функционал (для обратной совместимости)
        width = session.get("portal_width")
        height = session.get("portal_height")
        has_rain = session.get("has_rain")
        color = session.get("color")
        hardware = session.get("hardware")
        glazing = session.get("glazing")
        schemes = session.get("schemes")
        wood_type = session.get("wood_type")

        if schemes and width and height:
            data, labor_data = calculate_beams(
                portal_width=width,
                portal_height=height,
                has_rain=has_rain,
                hardware=hardware,
                color=color,
                glass_type=glazing,
                schemes=schemes,
                wood_type=wood_type,
            )
            context["data"] = data
            context["labor_data"] = labor_data
            context["portal_width"] = width
            context["portal_height"] = height

        return context
