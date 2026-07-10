from json import dumps, loads

from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.generic import DetailView, ListView, View

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
from calculate.services import calculate_glukhar, calculate_portals
from core.mixins import AdminRequiredMixin, ManagerRequiredMixin
from orders.models import Order
from users.models import Buyer


def serialize_product(instance):
    exclude = {"id", "order", "calculation_details"}
    result = {}
    for field in instance._meta.fields:
        if field.name in exclude:
            continue

        value = getattr(instance, field.name)
        if field.is_relation and value is not None:
            value = str(value)
        elif isinstance(value, bool):
            value = "Да" if value else "Нет"
        elif value is None:
            value = "-"

        result[str(field.verbose_name)] = value

    return result


class OrderListView(ListView, AdminRequiredMixin):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders_data"

    def get_queryset(self):
        return Order.objects.select_related("buyer").order_by("-created_at")


class OrderDetailView(DetailView, AdminRequiredMixin):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("buyer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["portals"] = self.object.portal_set.all()
        context["glukhars"] = self.object.glukhar_set.all()
        return context


class OrderEditView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = "orders/edit.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("buyer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        portals = self.object.portal_set.select_related(
            "color_type",
            "glass",
            "wood_type",
            "scheme",
            "hardware_type",
        )
        glukhars = self.object.glukhar_set.select_related("color_type", "wood_type")

        items = []
        details_by_key = {}

        for portal in portals:
            key = f"portal-{portal.id}"
            items.append(
                {
                    "key": key,
                    "id": portal.id,
                    "type": "portal",
                    "type_label": "Портал",
                    "title":
                        f"Портал {portal.width}×{portal.height}, {portal.amount} шт.",
                    "is_finished": portal.is_finished,
                },
            )
            details_by_key[key] = serialize_product(portal)

        for glukhar in glukhars:
            key = f"glukhar-{glukhar.id}"
            items.append(
                {
                    "key": key,
                    "id": glukhar.id,
                    "type": "glukhar",
                    "type_label": "Глухарь",
                    "title":
                        f"Глухарь {glukhar.width}×{glukhar.height}, {glukhar.amount} шт.",
                    "is_finished": glukhar.is_finished,
                },
            )
            details_by_key[key] = serialize_product(glukhar)

        context["items"] = items
        context["details_json"] = dumps(details_by_key, default=str)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = loads(request.body)

        item_type = data.get("type")
        item_id = data.get("id")
        is_finished = bool(data.get("is_finished"))

        model = {"portal": Portal, "glukhar": Glukhar}.get(item_type)
        if model is None:
            return JsonResponse(
                {"status": "error", "message": "Неизвестный тип элемента"},
                status=400,
            )

        updated = model.objects.filter(id=item_id, order=self.object).update(
            is_finished=is_finished,
        )
        if not updated:
            raise Http404("Элемент заказа не найден")

        order_finished = not (
            self.object.portal_set.filter(is_finished=False).exists()
            or self.object.glukhar_set.filter(is_finished=False).exists()
        )
        if order_finished != self.object.is_finished:
            self.object.is_finished = order_finished
            self.object.save(update_fields=["is_finished"])

        return JsonResponse(
            {"status": "success", "order_is_finished": self.object.is_finished},
        )


class OrderFormView(ManagerRequiredMixin, View):
    def get(self, request):
        portal_ratio = float(ProfitRatio.objects.get(name="portal").ratio)
        glukhar_ratio = float(ProfitRatio.objects.get(name="glukhar").ratio)

        schemes = list(Scheme.objects.values("id", "name", "min_size", "max_size"))

        context = {
            "portal_profit_ratio": portal_ratio,
            "glukhar_profit_ratio": glukhar_ratio,
            "schemes_json": dumps(schemes),
        }
        return render(request, "orders/combined_order_form.html", context)


class CombinedOrderSaveView(ManagerRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        config = data.get("config", {})
        calculations = data.get("calculations", {})
        portal_calc_results = calculations.get("portals", {})
        glukhar_calc_results = calculations.get("glukhars", {})

        portals = config.get("portals", [])
        glukhars = config.get("glukhars", [])

        if not portals and not glukhars:
            return JsonResponse(
                {"status": "error", "error": "В заказе нет ни одной позиции"},
                status=400,
            )

        buyer_id = config.get("buyer_id")

        installation = int(config.get("installation", 0))
        delivery = int(config.get("delivery", 0))
        unloading = int(config.get("unloading", 0))
        discount = int(config.get("discount", 0))

        buyer = None
        if buyer_id not in (None, "null", "new"):
            buyer = Buyer.objects.get(id=buyer_id)
        elif buyer_id == "new":
            buyer_data = config.get("buyer_data", {})
            with transaction.atomic():
                buyer = Buyer.objects.create(**buyer_data)

        with transaction.atomic():
            order = Order.objects.create(
                delivery=delivery,
                installation=installation,
                unloading=unloading,
                discount=discount,
                creator=request.user,
                buyer=buyer,
            )

            for portal in portals:
                scheme_obj = Scheme.objects.get(name=portal["scheme"])
                wood_obj = PortalWood.objects.get(name=portal["wood_type"].lower())
                hardware_obj = Hardware.objects.get(name=portal["hardware"])
                glass_obj = Glass.objects.get(name=portal["glazing"])
                color_type = Color.objects.get(name=portal["color"])

                Portal.objects.create(
                    width=portal["width"],
                    height=portal["height"],
                    has_rain_protection=portal["has_rain"],
                    color_type=color_type,
                    hardware_type=hardware_obj,
                    scheme=scheme_obj,
                    wood_type=wood_obj,
                    hardware_color=portal["hardware_color"],
                    glass=glass_obj,
                    order=order,
                    amount=portal["amount"],
                    calculation_details=portal_calc_results[portal["name"]],
                )

            for glukhar in glukhars:
                wood_type = GlukharWood.objects.get(name=glukhar["material"])
                color_type = Color.objects.get(name=glukhar["color"])

                Glukhar.objects.create(
                    width=int(glukhar["width"]),
                    height=int(glukhar["height"]),
                    wood_type=wood_type,
                    color_type=color_type,
                    is_non_rectangular=glukhar["is_not_rectangle"],
                    order=order,
                    amount=glukhar["amount"],
                    calculation_details=glukhar_calc_results[glukhar["name"]],
                )

        return JsonResponse({"status": "success", "order_id": order.id})


class GlukharOrderView(ManagerRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="glukhar")
        profit_ratio = float(ratio_obj.ratio)

        return render(request, "orders/glukhar.html", {"profit_ratio": profit_ratio})

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        glukhars = data.get("glukhars", [])
        calc_result = calculate_glukhar(glukhars)

        ratio_obj = ProfitRatio.objects.get(name="glukhar")
        calc_result["profit_ratio"] = float(ratio_obj.ratio)

        if request.user.profile.is_manager:
            calc_result["dealer_percent"] = request.user.percentage_sale

        return JsonResponse(calc_result)


class SaveGlukharOrderView(ManagerRequiredMixin, View):
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
                creator=request.user,
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


class PortalOrderView(ManagerRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="portal")
        profit_ratio = float(ratio_obj.ratio)

        schemes = list(Scheme.objects.values("id", "name", "min_size", "max_size"))
        context = {
            "profit_ratio": profit_ratio,
            "schemes_json": dumps(schemes),
        }
        return render(request, "orders/portal.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        portals = data.get("portals", [])
        calc_result = calculate_portals(portals)

        ratio_obj = ProfitRatio.objects.get(name="portal")
        calc_result["profit_ratio"] = float(ratio_obj.ratio)

        if request.user.profile.is_manager:
            calc_result["dealer_percent"] = request.user.percentage_sale

        return JsonResponse(calc_result)


class PortalOrderSaveView(ManagerRequiredMixin, View):
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
                creator=request.user,
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
