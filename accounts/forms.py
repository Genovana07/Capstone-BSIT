from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ServicePackage

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Ensure email is required

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ServicePackageForm(forms.ModelForm):
    class Meta:
        model = ServicePackage
        fields = ['title', 'description', 'price', 'image', 'equipment']