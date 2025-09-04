from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path("", views.category_list, name="list"),
    path("category/<slug:slug>",
         views.product_list_by_category, name="category"),
    path("<slug:slug>", views.product_detail, name="detail"),
]
