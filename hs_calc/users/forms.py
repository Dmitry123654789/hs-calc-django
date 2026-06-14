import django.contrib.auth.forms
import django.db.transaction
import django.forms
import phonenumber_field.formfields

import users.models


class CustomUserCreationForm(django.forms.ModelForm):
    role = django.forms.ChoiceField(
        choices=users.models.Profile.Role.choices,
        label="Роль",
        initial=users.models.Profile.Role.GROUP_MANAGER,
        widget=django.forms.Select(attrs={"class": "form-select"}),
    )

    phone = phonenumber_field.formfields.PhoneNumberField(
        label="Телефон",
        required=False,
        region="RU",
    )

    percentage_sale = django.forms.IntegerField(
        label="Процент_с_продажи",
        required=False,
        initial=10,
        widget=django.forms.NumberInput(attrs={"min": 0, "max": 100}),
    )

    password1 = django.forms.CharField(
        label="Пароль",
        widget=django.forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = users.models.CustomUser
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя_пользователя"
        self.fields["password1"].label = "Пароль"

    def save(self, commit=True):
        with django.db.transaction.atomic():
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


class CustomAuthenticationForm(django.contrib.auth.forms.AuthenticationForm):
    username = django.forms.CharField(
        label="Имя_пользователя",
        widget=django.forms.TextInput(attrs={"autofocus": True}),
    )
    password = django.forms.CharField(
        label="Пароль",
        strip=False,
        widget=django.forms.PasswordInput(
            attrs={"autocomplete": "current-password"},
        ),
    )

    error_messages = {
        "invalid_login": "Пожалуйста,_введите_правильные_имя_пользователя_и_пароль.",
    }


class CustomPasswordChangeForm(django.contrib.auth.forms.PasswordChangeForm):
    old_password = django.forms.CharField(
        label="Старый_пароль",
        strip=False,
        widget=django.forms.PasswordInput(
            attrs={"autocomplete": "current-password", "autofocus": True},
        ),
    )
    new_password1 = django.forms.CharField(
        label="Новый_пароль",
        widget=django.forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
        strip=False,
    )
    new_password2 = django.forms.CharField(
        label="Подтверждение_нового_пароля",
        strip=False,
        widget=django.forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
    )
