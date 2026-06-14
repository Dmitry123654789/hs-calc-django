import django.contrib.auth.mixins
import django.shortcuts
import django.urls


class ForbiddenMixin(
    django.contrib.auth.mixins.LoginRequiredMixin,
    django.contrib.auth.mixins.UserPassesTestMixin,
):
    fallback_url = django.urls.reverse_lazy("pages:home")

    def handle_no_permission(self):
        return django.shortcuts.redirect(self.fallback_url)
