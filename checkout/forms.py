from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone_number',
            'address1', 'address2', 'city',
            'county', 'postcode', 'country',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'address1': forms.TextInput(attrs={'placeholder': 'House/Street'}),
            'address2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc (optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'City/Town'}),
            'county': forms.TextInput(attrs={'placeholder': 'County/State (optional)'}),
            'postcode': forms.TextInput(attrs={'placeholder': 'Postcode/ZIP'}),
        }
