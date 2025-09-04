from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category, Product


def category_list(request):
    """ A view to show categories """
    categories = Category.objects.filter(
        is_active=True).order_by('sort_order', 'name')
    # To show a few latest active products
    latest_products = Product.objects.filter(
        is_active=True).order_by('-created_at')[:8]
    return render(request, 'products/category_list.html', {
        'categories': categories,
        'latest_products': latest_products,
    })


def product_list_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    product_qs = (
        Product.objects.filter(
            is_active=True, category=category).prefetch_related(
                'images').order_by('name')
    )
    paginator = Paginator(product_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'products/product_list.html', {
        'category': category,
        'page_obj': page_obj,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('images'), slug=slug, is_active=True)
    # This picks primary image or first as fallback
    primary = product.images.filter(
        is_primary=True).first() or product.images.first()
    gallery = list(product.images.all())

    gallery_js = []
    if primary:
        gallery_js.append({
            'url': primary.image.url,
            'alt': primary.alt_text or product.name,
        })
    for img in gallery:
        if not any(g['url'] == img.image.url for g in gallery_js):
            gallery_js.append({
                'url': img.image.url,
                'alt': img.alt_text or product.name,
            })


    return render(request, 'products/product_detail.html', {
        'product': product,
        'primary_image': primary,
        'gallery': gallery,
        'gallery_js': gallery_js,
    })
