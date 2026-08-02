from django.urls import path

from calculate import views

app_name = "calculate"

urlpatterns = [
    path("markup/", views.MarkupView.as_view(), name="markup"),
]
