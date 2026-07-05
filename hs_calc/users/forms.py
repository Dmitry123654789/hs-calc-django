from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db import transaction
from phonenumber_field.formfields import PhoneNumberField

from users.models import Buyer, CustomUser, Profile


class CustomUserCreationForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.Role.choices,
        label="Роль",
        initial=Profile.Role.GROUP_MANAGER,
    )

    phone = PhoneNumberField(
        label="Телефон",
        required=False,
        region="RU",
    )

    percentage_sale = forms.IntegerField(
        label="Процент с продажи",
        required=False,
        initial=10,
        min_value=0,
        max_value=100,
    )

    password1 = forms.CharField(
        label="Пароль",
    )

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя пользователя"

    def save(self, commit=True):
        with transaction.atomic():
            user = super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])

            if commit:
                user.save()
                user.refresh_from_db()
                profile = user.profile

                profile.role = self.cleaned_data.get("role")
                profile.phone = self.cleaned_data.get("phone", None)

                if not profile.is_manager:
                    profile.percentage_sale = None
                else:
                    profile.percentage_sale = self.cleaned_data.get(
                        "percentage_sale",
                    )

                profile.save()

            return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя_пользователя",
        widget=forms.TextInput(attrs={"autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"},
        ),
    )

    error_messages = {
        "invalid_login": "Пожалуйста, введите правильные имя пользователя и пароль.",
    }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Старый_пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True},
        ),
    )
    new_password1 = forms.CharField(
        label="Новый_пароль",
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Подтверждение_нового_пароля",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
    )


class BuyerForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ("first_name", "last_name", "phone", "email")
