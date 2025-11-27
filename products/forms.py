from django import forms
from django.forms import inlineformset_factory

from .models import Product, ProductReview, ProductImage


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
            "body": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
        }


class ProductImageForm(forms.ModelForm):
    """
    Form for managing a single ProductImage in the admin UI.
    """

    class Meta:
        model = ProductImage
        fields = ["image", "alt_text", "is_primary", "sort_order"]
        widgets = {
            "alt_text": forms.TextInput(
                attrs={"placeholder": "Optional alt text (for accessibility)"}
            ),
            "sort_order": forms.NumberInput(attrs={"min": 0}),
        }


ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,           # one empty form by default
    can_delete=True,   # allow removing images on edit
    validate_min=False,
    validate_max=False,
)
