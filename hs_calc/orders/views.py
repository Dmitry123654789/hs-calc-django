from decimal import Decimal, ROUND_HALF_UP
from json import dumps, loads

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
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
from core.mixins import BackURLMixin, ManagerRequiredMixin, OnlyWorkerRequiredMixin
from orders.kp_export import build_commercial_proposal
from orders.models import Order
from users.models import Buyer


ORDER_STATUS_TRANSITIONS = {
    Order.Status.Ordered: {Order.Status.In_work, Order.Status.Cancelled},
    Order.Status.In_work: {Order.Status.Done, Order.Status.Cancelled},
}
REPLACE_DICT = {
    "hardware": "Фурнитура",
    "ral_enamel": "RAL-эмаль",
    "ral_primer": "RAL-грунт",
    "glass_doors": "Стеклопакет створка",
    "glass_sashes": "Стеклопакет глухарь",
    "sash": "Створка",
    "lock": "Замок",
    "packaging": "Упаковка",
    "glass": "Стеклопакет",
    "carpenter": "Столяр",
    "painter": "Маляр",
    "glaze_varnish": "Лесс-лак",
    "glaze_primer": "Лесс-грунт",
}


def calculate_dealer_percentage(user):
    if user.profile.is_manager:
        return user.profile.percentage_sale

    return 0


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


class OrderListView(ListView, LoginRequiredMixin):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders_data"

    def get_queryset(self):
        queryset = Order.objects.select_related("buyer").order_by("-created_at")
        user = self.request.user

        if user.profile.is_worker:
            return queryset.filter(status=Order.Status.In_work)

        return queryset


class OrderDetailView(BackURLMixin, ManagerRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("buyer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["portals"] = self.object.portal_set.all()
        context["glukhars"] = self.object.glukhar_set.all()
        context["back_url"] = self.get_back_url()

        dealer_percentage = self.object.percentage_worker or Decimal("0")
        total_sum = self.object.total_sum or Decimal("0")
        dealer_amount = (dealer_percentage / Decimal("100")) * total_sum
        context["dealer_amount"] = dealer_amount.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
        context["replace_dict"] = REPLACE_DICT
        return context


class OrderDownloadKPView(ManagerRequiredMixin, View):
    """Отдает .docx коммерческое предложение по заказу для скачивания."""

    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order.objects.select_related("buyer"), pk=pk)

        buffer = build_commercial_proposal(order)

        response = HttpResponse(
            buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="KP_order_{order.pk}.docx"'
        )
        return response


class OrderDetailMaterialsView(BackURLMixin, OnlyWorkerRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail_materials.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["portals"] = self.object.portal_set.all()
        context["glukhars"] = self.object.glukhar_set.all()
        context["back_url"] = self.get_back_url()
        context["replace_dict"] = REPLACE_DICT
        return context


class OrderEditView(BackURLMixin, DetailView):
    model = Order
    template_name = "orders/edit.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("buyer")

    def _all_items_finished(self):
        return not (
            self.object.portal_set.filter(is_finished=False).exists()
            or self.object.glukhar_set.filter(is_finished=False).exists()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["back_url"] = self.get_back_url()

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
                    "title": f"Портал {portal.width}×{portal.height}, "
                    f"{portal.amount} шт.",
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
                    "title": f"Глухарь {glukhar.width}×{glukhar.height}, "
                    f"{glukhar.amount} шт.",
                    "is_finished": glukhar.is_finished,
                },
            )
            details_by_key[key] = serialize_product(glukhar)

        context["items"] = items
        context["details_json"] = dumps(details_by_key, default=str)

        context["can_toggle_items"] = self.object.status == Order.Status.In_work
        context["all_items_finished"] = self._all_items_finished()
        context["available_transitions"] = [
            {"value": status, "label": Order.Status(status).label}
            for status in ORDER_STATUS_TRANSITIONS.get(self.object.status, set())
        ]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = loads(request.body)

        if data.get("type") == "status":
            return self._handle_status_change(data)

        return self._handle_item_toggle(data)

    def _handle_item_toggle(self, data):
        item_type = data.get("type")
        item_id = data.get("id")
        is_finished = bool(data.get("is_finished"))

        if not self.object.status == Order.Status.In_work:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Нельзя отмечать элементы заказа, неверный статус заказа",
                },
                status=400,
            )

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

        return JsonResponse(
            {
                "status": "success",
                "order_status": self.object.status,
                "all_items_finished": self._all_items_finished(),
            },
        )

    def _handle_status_change(self, data):
        new_status = data.get("status")
        allowed = ORDER_STATUS_TRANSITIONS.get(self.object.status, set())

        if new_status not in allowed:
            return JsonResponse(
                {"status": "error", "message": "Недопустимый переход статуса"},
                status=400,
            )

        if new_status == Order.Status.Done and not self._all_items_finished():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Нельзя завершить заказ: не все элементы "
                    "отмечены как выполненные",
                },
                status=400,
            )

        self.object.status = new_status
        self.object.save(update_fields=["status"])

        return JsonResponse({"status": "success", "order_status": self.object.status})


class OrderFormView(ManagerRequiredMixin, View):
    def get(self, request):
        schemes = list(
            Scheme.objects.values("id", "name", "min_size", "max_size", "ratio"),
        )

        is_admin = request.user.profile.is_director
        dealer_percentage = (
            0 if is_admin else float(request.user.profile.percentage_sale or 0)
        )

        context = {
            "schemes_json": dumps(schemes, default=str),
            "is_admin": is_admin,
            "dealer_percentage": dealer_percentage,
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

        order_total = config.get("order_total", 0)
        percentage_worker = calculate_dealer_percentage(request.user)

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
                percentage_worker=percentage_worker,
                total_sum=order_total,
            )

            for portal in portals:
                scheme_obj = Scheme.objects.get(name=portal["scheme"])
                wood_obj = PortalWood.objects.get(name=portal["wood_type"].lower())
                hardware_obj = Hardware.objects.get(name=portal["hardware"])
                glass_obj = Glass.objects.get(name=portal["glazing"])
                color_type = Color.objects.get(name=portal["color"])

                portal_details = dict(portal_calc_results[portal["name"]])

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
                    calculation_details=portal_details,
                )

            for glukhar in glukhars:
                wood_type = GlukharWood.objects.get(name=glukhar["material"])
                color_type = Color.objects.get(name=glukhar["color"])

                glukhar_details = dict(glukhar_calc_results[glukhar["name"]])

                Glukhar.objects.create(
                    width=int(glukhar["width"]),
                    height=int(glukhar["height"]),
                    wood_type=wood_type,
                    color_type=color_type,
                    is_non_rectangular=glukhar["is_not_rectangle"],
                    order=order,
                    amount=glukhar["amount"],
                    calculation_details=glukhar_details,
                )

        return JsonResponse({"status": "success", "order_id": order.id})


class GlukharOrderView(ManagerRequiredMixin, View):
    def get(self, request):
        ratio_obj = ProfitRatio.objects.get(name="glukhar")
        profit_ratio = float(ratio_obj.ratio)

        is_admin = request.user.profile.is_director
        dealer_percentage = (
            0 if is_admin else float(request.user.profile.percentage_sale or 0)
        )

        context = {
            "profit_ratio": profit_ratio,
            "is_admin": is_admin,
            "dealer_percentage": dealer_percentage,
        }
        return render(request, "orders/glukhar.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        glukhars = data.get("glukhars", [])

        ratio = float(ProfitRatio.objects.get(name="glukhar").ratio)
        calc_result = calculate_glukhar(glukhars, ratio)

        calc_result["profit_ratio"] = ratio

        if not request.user.profile.is_director:
            calc_result["dealer_percentage"] = float(
                request.user.profile.percentage_sale or 0,
            )

        return JsonResponse(calc_result)


class GlukharOrderSaveView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        config = data.get("config")
        calc_results = data.get("calculations")

        buyer_id = config["buyer_id"]

        installation = int(config.get("installation", 0))
        delivery = int(config.get("delivery", 0))
        unloading = int(config.get("unloading", 0))
        discount = int(config.get("discount", 0))

        order_total = config.get("order_total", 0)
        percentage_worker = calculate_dealer_percentage(request.user)

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
                percentage_worker=percentage_worker,
                total_sum=order_total,
            )

            for glukhar in config["glukhars"]:
                width = glukhar["width"]
                height = glukhar["height"]
                amount = glukhar["amount"]
                is_not_rect = glukhar["is_not_rectangle"]

                wood_type = GlukharWood.objects.get(name=glukhar["material"])
                color_type = Color.objects.get(name=glukhar["color"])

                key = glukhar["name"]

                glukhar_details = dict(calc_results[key])
                Glukhar.objects.create(
                    width=int(width),
                    height=int(height),
                    wood_type=wood_type,
                    color_type=color_type,
                    is_non_rectangular=is_not_rect,
                    order=order,
                    amount=amount,
                    calculation_details=glukhar_details,
                )

        return JsonResponse({"status": "success", "order_id": order.id})


class PortalOrderView(ManagerRequiredMixin, View):
    def get(self, request):
        schemes = list(
            Scheme.objects.values("id", "name", "min_size", "max_size", "ratio"),
        )

        is_admin = request.user.profile.is_director
        dealer_percentage = (
            0 if is_admin else float(request.user.profile.percentage_sale or 0)
        )

        context = {
            "schemes_json": dumps(schemes, default=str),
            "is_admin": is_admin,
            "dealer_percentage": dealer_percentage,
        }
        return render(request, "orders/portal.html", context)

    def post(self, request, *args, **kwargs):
        data = loads(request.body)

        portals = data.get("portals", [])
        calc_result = calculate_portals(portals)

        if not request.user.profile.is_director:
            calc_result["dealer_percentage"] = float(
                request.user.profile.percentage_sale or 0,
            )

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

        order_total = config.get("order_total", 0)
        percentage_worker = calculate_dealer_percentage(request.user)

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
                percentage_worker=percentage_worker,
                total_sum=order_total,
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

                portal_details = dict(calc_results[name])

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
                    calculation_details=portal_details,
                )

        return JsonResponse({"status": "success", "order_id": order.id})
