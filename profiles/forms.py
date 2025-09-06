from django import forms
from django_countries.widgets import CountrySelectWidget
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'address1', 'address2',
            'city', 'county', 'postcode', 'country'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'address1': forms.TextInput(attrs={'placeholder': 'House/Street'}),
            'address2': forms.TextInput(attrs={'placeholder': 'Apartment, Suite, etc (optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'City/Town'}),
            'county': forms.TextInput(attrs={'placeholder': 'County/State (optional)'}),
            'postcode': forms.TextInput(attrs={'placeholder': 'Postcode/ZIP'}),
            'country': CountrySelectWidget,
        }
