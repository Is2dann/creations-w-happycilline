from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path("", views.category_list, name="category_list"),  # /products/
    path("category/<slug:slug>", views.product_list_by_category, name="product_list_by_category"),
    path("item/<slug:slug>", views.product_detail, name="product_detail"),
]