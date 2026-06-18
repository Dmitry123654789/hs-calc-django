from json import dumps, loads

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, View

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
from calculate.services import calculate_beams, calculate_glukhar, calculate_portals
from orders.models import Order
from users.models import Buyer


class GlukharOrderView(LoginRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="glukhar")
        profit_ratio = float(ratio_obj.ratio)

        return render(request, "calculate/glukhar.html", {"profit_ratio": profit_ratio})

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        glukhars = data.get("glukhars", [])
        calc_result = calculate_glukhar(glukhars)
        return JsonResponse(calc_result)


class SaveGlukharOrderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        config = data.get("config")
        calc_results = data.get("calculations")

        buyer_id = config["buyer_id"]

        installation = int(config.get("installation", 0))
        delivery = int(config.get("delivery", 0))
        unloading = int(config.get("unloading", 0))
        discount = int(config.get("discount", 0))

        buyer = None
        if buyer_id not in ["null", "new"]:
            buyer = Buyer.objects.get(id=buyer_id)
        elif buyer_id == "new":
            buyer_data = config["buyer_data"]
            with transaction.atomic():
                buyer = Buyer.objects.create(**buyer_data)

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
            for glukhar in config["glukhars"]:
                width = glukhar["width"]
                height = glukhar["height"]
                amount = glukhar["amount"]
                is_not_rect = glukhar["is_not_rectangle"]

                wood_type = GlukharWood.objects.get(name=glukhar["material"])
                color_type = Color.objects.get(name=glukhar["color"])

                key = glukhar["name"]

                Glukhar.objects.create(
                    width=int(width),
                    height=int(height),
                    wood_type=wood_type,
                    color_type=color_type,
                    is_non_rectangular=is_not_rect,
                    order=order,
                    amount=amount,
                    calculation_details=calc_results[key],
                )

        return JsonResponse({"status": "success"})


class PortalOrderView(LoginRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="portal")
        profit_ratio = float(ratio_obj.ratio)

        schemes = list(Scheme.objects.values("id", "name", "min_size", "max_size"))
        context = {
            "profit_ratio": profit_ratio,
            "schemes_json": dumps(schemes),
        }
        return render(request, "calculate/portal_order.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        portals = data.get("portals", [])
        calc_result = calculate_portals(portals)
        return JsonResponse(calc_result)


class PortalOrderSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        config = data.get("config")
        calc_results = data.get("calculations")

        buyer_id = config["buyer_id"]

        installation = int(config.get("installation", 0))
        delivery = int(config.get("delivery", 0))
        unloading = int(config.get("unloading", 0))
        discount = int(config.get("discount", 0))

        buyer = None
        if buyer_id not in ["null", "new"]:
            buyer = Buyer.objects.get(id=buyer_id)
        elif buyer_id == "new":
            buyer_data = config["buyer_data"]
            with transaction.atomic():
                buyer = Buyer.objects.create(**buyer_data)

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
            for portal in config["portals"]:
                width = portal["width"]
                height = portal["height"]
                has_rain = portal["has_rain"]
                hardware_color = portal["hardware_color"]
                amount = portal["amount"]
                width = portal["width"]
                name = portal["name"]

                scheme_obj = Scheme.objects.get(name=portal["scheme"])
                wood_obj = PortalWood.objects.get(name=portal["wood_type"].lower())
                hardware_obj = Hardware.objects.get(name=portal["hardware"])
                glass_obj = Glass.objects.get(name=portal["glazing"])
                color_type = Color.objects.get(name=portal["color"])

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
                    calculation_details=calc_results[name],
                )

        return JsonResponse({"status": "success"})


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
            scheme = schemes[0] if isinstance(schemes, list) else schemes
            data, labor_data, portal_total = calculate_beams(
                portal_width=width,
                portal_height=height,
                has_rain=has_rain,
                hardware=hardware,
                color=color,
                glass_type=glazing,
                scheme=scheme,
                wood_type=wood_type,
                hardware_color="white",
                amount=1,
            )
            context["data"] = data
            context["labor_data"] = labor_data
            context["portal_width"] = width
            context["portal_height"] = height

        return context
