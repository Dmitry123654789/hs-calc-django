from django.urls import path

from calculate import views

app_name = "calculate"

urlpatterns = [
    path("glukhar-order/", views.GlukharOrderView.as_view(), name="glukhar_order"),
    path("glukhar/save/", views.SaveGlukharOrderView.as_view(), name="glukhar_save"),
    path("portal-order/", views.PortalOrderView.as_view(), name="portal_order"),
    path(
        "portal-order/save/",
        views.PortalOrderSaveView.as_view(),
        name="portal_order_save",
    ),
    path("result/", views.ResultView.as_view(), name="result"),
]
