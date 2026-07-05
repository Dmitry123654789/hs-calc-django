from django.urls import path

from about.views import DescriptionView


app_name = "about"


urlpatterns = [
    path(
        "",
        DescriptionView.as_view(),
        name="home",
    ),
]
