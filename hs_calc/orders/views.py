from django.views.generic import DetailView, ListView

from orders.models import Order


class OrderListView(ListView):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders_data"

    def get_queryset(self):
        return Order.objects.select_related("buyer").order_by("-created_at")


class OrderDetailView(DetailView):
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
