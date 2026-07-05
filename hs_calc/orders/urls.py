from django.urls import path

from orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="orders_list"),
    path("<int:pk>/detail/", views.OrderDetailView.as_view(), name="orders_detail"),
    path("<int:pk>/edit/", views.OrderEditView.as_view(), name="orders_edit"),
]
