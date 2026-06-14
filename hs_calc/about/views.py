import django.views.generic


class DescriptionView(django.views.generic.TemplateView):
    template_name = "about/home.html"
