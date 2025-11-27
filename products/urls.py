from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Admin / staff product management
    path(
        "admin/products/",
        views.admin_product_list,
        name="admin_product_list",
    ),
    path(
        "admin/products/add/",
        views.product_create,
        name="product_create",
    ),
    path(
        "admin/products/<int:pk>/edit/",
        views.product_update,
        name="product_update",
    ),
    path(
        "admin/products/<int:pk>/delete/",
        views.product_delete,
        name="product_delete",
    ),

    # Wishlist
    path(
        "wishlist/",
        views.wishlist_list,
        name="wishlist",
    ),
    path(
        "wishlist/toggle/<int:product_id>/",
        views.wishlist_toggle,
        name="wishlist_toggle",
    ),

    # Product review
    path(
        "<slug:slug>/review/",
        views.product_review,
        name="product_review",
    ),

    # Public catalog
    path("", views.product_list, name="list"),
    path(
        "category/<slug:slug>",
        views.product_list_by_category,
        name="category",
    ),
    path("<slug:slug>", views.product_detail, name="detail"),
]
