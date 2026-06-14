from django import forms

from calculate.models import Scheme


class CalculationForm(forms.Form):
    width = forms.IntegerField(
        min_value=1200,
        max_value=15000,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "id": "id_width"},
        ),
    )
    height = forms.IntegerField(
        min_value=2100,
        max_value=3000,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    wood_type = forms.ChoiceField(
        label="Тип дерева",
        choices=[("Сосна", "Сосна"), ("Лиственница", "Лиственница"), ("Дуб", "Дуб")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    has_rain = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"},
        ),
    )
    color = forms.ChoiceField(
        choices=[("RAL", "RAL"), ("Лесс", "Лесс")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    hardware = forms.ChoiceField(
        choices=[("Standard", "Односторонняя"), ("Standard+", "Двусторонняя")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    glazing = forms.ChoiceField(
        choices=[("Standard", "Standard"), ("Standard+", "Standard+")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    scheme = forms.ChoiceField(
        label="Выберите схему",
        choices=[],
        required=True,
        error_messages={"required": "Пожалуйста, выберите одну из доступных схем."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        schemes = Scheme.objects.all()
        self.fields["scheme"].choices = [(s.name, s.name) for s in schemes]
        self.schemes_data = list(
            schemes.values("id", "name", "min_size", "max_size"),
        )
