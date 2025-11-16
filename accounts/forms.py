from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory  # Note: inlineformset_factory is imported but not used in the provided code
from .models import ServicePackage, PackageEquipment, Equipment

class CustomUserCreationForm(UserCreationForm):
    """
    A custom user creation form that adds the 'email' field as required.
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")  # ✅ Corrected


class ServicePackageForm(forms.ModelForm):
    """
    Form for creating and updating ServicePackage objects.
    """
    class Meta:
        model = ServicePackage
        fields = ['title', 'description', 'price', 'image', 'category']


class EquipmentQuantityForm(forms.Form):
    """
    A dynamic form to select quantities for a given list of Equipment objects.
    """
    def __init__(self, *args, **kwargs):
        equipments = kwargs.pop('equipments')
        super().__init__(*args, **kwargs)

        # Dynamically create a PositiveIntegerField for each equipment item
        for equipment in equipments:
            self.fields[f"equipment_{equipment.id}"] = forms.IntegerField(
                label=equipment.name,
                required=False,
                min_value=0,
                initial=0,
                help_text="Enter required quantity (0 if not included)"
            )