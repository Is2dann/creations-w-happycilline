from django.shortcuts import render
from django.contrib import messages
from products.models import Category, Product


def index(request):
    """
    Renders the homepage with featured
    categories and latest products
    """
    if request.GET.get('welcome') == '1':
        messages.success(request, 'Welcome back! Explore our latest creations.')

    categories = Category.objects.filter(
        is_active=True).order_by('sort_order', 'name')[:8]
    latest_products = Product.objects.filter(
        is_active=True).order_by('-created_at')[:8]
    
    context = {
        'categories': categories,
        'latest_products': latest_products,
    }

    return render(request, 'home/index.html', context)
