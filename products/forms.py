from django import forms
from .models import Product, ProductReview


class ProductForm(forms.ModelForm):
    """
    Simple form for creating and editing products via the UI.
    """
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "slug",
            "description",
            "price",
            "sku",
            "is_active",
        ]


class ProductReviewForm(forms.ModelForm):
    """
    Form for users to leave or update a review on a product.
    """
    class Meta:
        model = ProductReview
        fields = ["rating", "title", "body"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
