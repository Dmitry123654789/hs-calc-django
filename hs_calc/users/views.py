from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
    PasswordChangeDoneView as DjangoPasswordChangeDoneView,
    PasswordChangeView as DjangoPasswordChangeView,
)
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    View,
)
from django.views.generic.edit import FormMixin

from orders.models import Order
from users.forms import (
    BuyerForm,
    CustomAuthenticationForm,
    CustomPasswordChangeForm,
    CustomUserCreationForm,
)
from users.mixins import AdminRequiredMixin
from users.models import Buyer, CustomUser, Profile


class RegisterView(
    AdminRequiredMixin,
    CreateView,
):
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:register")

    def test_func(self):
        return self.request.user.profile.is_director


class LoginView(DjangoLoginView):
    form_class = CustomAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("users:profile")

    def get(self, request, *args, **kwargs):
        params = request.GET
        if "username" in params:
            user = CustomUser.objects.filter(
                username=params["username"],
            )
            if not user:
                return super().get(self, request, *args, **kwargs)

            login(request, user[0])
            return HttpResponseRedirect(
                reverse("users:profile"),
            )

        return super().get(self, request, *args, **kwargs)


class LogoutView(DjangoLogoutView):
    template_name = "users/logout.html"
    next_page = reverse_lazy("users:login")


class PasswordChangeView(DjangoPasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:password_change_done")


class PasswordChangeDoneView(DjangoPasswordChangeDoneView):
    template_name = "users/password_change_done.html"


class ProfileView(
    LoginRequiredMixin,
    TemplateView,
):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["profile"] = self.request.user.profile
        return context


class AdminUserListView(AdminRequiredMixin, ListView):
    model = CustomUser
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
        valid_roles = [choice[0] for choice in Profile.Role.choices]
        if role_filter in valid_roles:
            return queryset.filter(profile__role=role_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = Profile.Role.choices
        context["current_role"] = self.request.GET.get("role", "")
        return context


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    model = CustomUser
    template_name = "users/admin_user_detail.html"
    context_object_name = "target_user"


class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    success_url = reverse_lazy("users:admin_user_list")


class BuyerListView(
    LoginRequiredMixin,
    View,
):
    """API для получения списка существующих покупателей"""

    def get(self, request, *args, **kwargs):
        buyers = Buyer.objects.all().values(
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

        return JsonResponse(list(buyers), safe=False)


class BuyerListCreateView(AdminRequiredMixin, FormMixin, ListView):
    model = Buyer
    template_name = "users/buyer_list.html"
    context_object_name = "buyers"
    form_class = BuyerForm
    success_url = reverse_lazy("users:buyers_list")

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class BuyerDetailView(AdminRequiredMixin, DetailView):
    model = Buyer
    template_name = "users/buyer_detail.html"
    context_object_name = "buyer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders_buyer = Order.objects.filter(buyer=self.object).order_by(
            "-created_at",
        )

        paginator = Paginator(orders_buyer, 10)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["orders_count"] = orders_buyer.count()
        return context


class BuyerDeleteView(AdminRequiredMixin, DeleteView):
    model = Buyer
    success_url = reverse_lazy("users:buyers_list")
