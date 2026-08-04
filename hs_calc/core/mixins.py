from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.profile.is_director

    def handle_no_permission(self):
        return redirect("403")


class ManagerRequiredMixin(AdminRequiredMixin):
    def test_func(self):
        user = self.request.user
        return super().test_func() or user.profile.is_manager


class OnlyWorkerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.profile.is_worker

    def handle_no_permission(self):
        return redirect("403")


class BackURLMixin:
    def get_back_url(self):
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url

        return reverse("orders:orders_list")
