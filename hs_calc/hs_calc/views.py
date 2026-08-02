from django.views.generic import TemplateView


class NotPermissionView(TemplateView):
    template_name = "errors/403.html"
