from json import dumps, loads

from django.http import Http404, JsonResponse
from django.views.generic import DetailView, ListView

from calculate.models import Glukhar, Portal
from core.mixins import AdminRequiredMixin
from orders.models import Order


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
