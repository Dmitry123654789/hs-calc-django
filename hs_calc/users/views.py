__all__ = ()

import django.contrib
import django.contrib.auth.mixins
import django.contrib.auth.views
import django.http
import django.urls
import django.views.generic

import users.forms
import users.models


class RegisterView(
    django.contrib.auth.mixins.LoginRequiredMixin,
    django.contrib.auth.mixins.UserPassesTestMixin,
    django.views.generic.CreateView,
):
    form_class = users.forms.CustomUserCreationForm
    template_name = "users/register.html"
    success_url = django.urls.reverse_lazy("users:register")

    def test_func(self):
        return self.request.user.profile.is_director


class LoginView(django.contrib.auth.views.LoginView):
    form_class = users.forms.CustomAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return django.urls.reverse_lazy("users:profile")

    def get(self, request, *args, **kwargs):
        params = request.GET
        if "username" in params:
            user = users.models.CustomUser.objects.filter(
                username=params["username"],
            )
            if not user:
                return super().get(self, request, *args, **kwargs)

            django.contrib.auth.login(request, user[0])
            return django.http.HttpResponseRedirect(
                django.urls.reverse("users:profile"),
            )

        return super().get(self, request, *args, **kwargs)


class LogoutView(django.contrib.auth.views.LogoutView):
    template_name = "users/logout.html"
    next_page = django.urls.reverse_lazy("users:login")


class PasswordChangeView(django.contrib.auth.views.PasswordChangeView):
    form_class = users.forms.CustomPasswordChangeForm
    template_name = "users/password_change.html"
    success_url = django.urls.reverse_lazy("users:password_change_done")


class PasswordChangeDoneView(django.contrib.auth.views.PasswordChangeDoneView):
    template_name = "users/password_change_done.html"


class ProfileView(
    django.contrib.auth.mixins.LoginRequiredMixin,
    django.views.generic.TemplateView,
):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["profile"] = self.request.user.profile
        return context


class AdminRequiredMixin(django.contrib.auth.mixins.UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "profile")
            and self.request.user.profile.is_director
        )


class AdminUserListView(AdminRequiredMixin, django.views.generic.ListView):
    model = users.models.CustomUser
    template_name = "users/admin_user_list.html"
    context_object_name = "users_list"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "profile",
            )
            .order_by(
                "username",
            )
        )

        role_filter = self.request.GET.get("role")
        valid_roles = [choice[0] for choice in users.models.Profile.Role.choices]
        if role_filter in valid_roles:
            return queryset.filter(profile__role=role_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = users.models.Profile.Role.choices
        context["current_role"] = self.request.GET.get("role", "")
        return context


class AdminUserDetailView(AdminRequiredMixin, django.views.generic.DetailView):
    model = users.models.CustomUser
    template_name = "users/admin_user_detail.html"
    context_object_name = "target_user"


class AdminUserDeleteView(AdminRequiredMixin, django.views.generic.DeleteView):
    model = users.models.CustomUser
    success_url = django.urls.reverse_lazy("users:admin_user_list")


class BuyerListView(
    django.contrib.auth.mixins.LoginRequiredMixin,
    django.views.generic.View,
):
    """API для получения списка существующих покупателей"""
    def get(self, request, *args, **kwargs):
        buyers = users.models.Buyer.objects.all().values(
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
        )
        data = []
        for b in buyers:
            if b["phone"]:
                b["phone"] = str(b["phone"])

            data.append(b)

        return django.http.JsonResponse(list(buyers), safe=False)
