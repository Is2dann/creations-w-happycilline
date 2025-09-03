from django.shortcuts import render
from products.models import Category, Product


def index(request):
    categories = Category.objects.filter(
        is_active=True).order_by('sort_order', 'name')[:8]
    latest_products = Product.objects.filter(
        is_active=True).order_by('-created_at')[:8]
    return render(request, 'home/index.html', {
        'categories': categories,
        'latest_products': latest_products,
    })
