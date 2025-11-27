from django.contrib import admin
from .models import Category, Product, ProductImage, Wishlist, ProductReview


class ProductImageInLine(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    inlines = [ProductImageInLine]
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('user', 'product')
    search_fields = ('user__username', 'product__name')
    ordering = ('-created_at',)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'approved', 'created_at')
    list_filter = ('rating', 'approved', 'product')
    search_fields = ('user__username', 'product__name', 'title')
    ordering = ('-created_at',)
