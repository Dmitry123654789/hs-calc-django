from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.profile.is_director


class ManagerRequiredMixin(AdminRequiredMixin):
    def test_func(self):
        user = self.request.user
        return super().test_func() or user.profile.is_manager
