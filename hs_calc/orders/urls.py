from django.urls import path

from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="orders_list"),
    path("<int:pk>/detail/", views.OrderDetailView.as_view(), name="orders_detail"),
    path("<int:pk>/edit/", views.OrderEditView.as_view(), name="orders_edit"),
    path("glukhar-order/", views.GlukharOrderView.as_view(), name="glukhar_order"),
    path(
        "glukhar-order/save/",
        views.SaveGlukharOrderView.as_view(),
        name="glukhar_order_save",
    ),
    path("portal-order/", views.PortalOrderView.as_view(), name="portal_order"),
    path(
        "portal-order/save/",
        views.PortalOrderSaveView.as_view(),
        name="portal_order_save",
    ),
    path("order/", views.OrderFormView.as_view(), name="combined_order_form"),
    path(
        "order/save/",
        views.CombinedOrderSaveView.as_view(),
        name="combined_order_save",
    ),
]
