from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404
from .models import Category, Product

# Map UI sort values to queryset order_by
SORT_MAP = {
    "newest": "-created_at",
    "name": "name",
    "-name": "-name",
    "price": "price",
    "-price": "-price",
}

PER_OPTIONS = [12, 24, 36, 48]


def category_list(request):
    categories = (
        Category.objects.filter(is_active=True)
        .annotate(
            product_count=Count("product", filter=Q(product__is_active=True)))
        .order_by("sort_order", "name")
    )
    latest_products = (
        Product.objects.filter(is_active=True)
        .order_by("-created_at")
        .prefetch_related("images")[:8]
    )
    return render(request, "products/category_list.html", {
        "categories": categories,
        "latest_products": latest_products,
    })


def _apply_catalog_filters(request, qs):
    """
    Apply search (?q=), sort (?sort=...),
    and pagination (?per=, ?page=) to a base queryset.
    Returns (page_obj, ctx_extras_dict).
    """
    # --- Search ---
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    # --- Sort ---
    sort_param = request.GET.get("sort") or "newest"
    qs = qs.order_by(SORT_MAP.get(sort_param, "-created_at"))

    # --- Pagination ---
    try:
        per_page = max(1, min(48, int(request.GET.get("per", "12"))))
    except ValueError:
        per_page = 12
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    return page_obj, {
        "q": q,
        "sort_param": sort_param,
        "per_page": per_page,
        "total": qs.count(),
    }


def product_list_by_category(request, slug):
    """
    List products in a single category with search/sort/pagination.
    Supports:
      ?q=phrase
      ?sort=newest|name|-name|price|-price
      ?per=12|24|36|48
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    base_qs = (
        Product.objects.filter(is_active=True, category=category)
        .prefetch_related('images')
        .select_related('category')
    )

    page_obj, extras = _apply_catalog_filters(request, base_qs)

    return render(request, 'products/product_list.html', {
        'category': category,
        'page_obj': page_obj,
        **extras,
        'per_options': PER_OPTIONS,
    })


def product_list(request):
    base_qs = (
        Product.objects.filter(is_active=True)
        .prefetch_related('images')
        .select_related('category')
    )

    # Optional category filter via query string (?category=<slug or id>)
    category_param = (request.GET.get("category") or "").strip()
    if category_param:
        if category_param.isdigit():
            base_qs = base_qs.filter(category_id=int(category_param))
        else:
            base_qs = base_qs.filter(category__slug=category_param)

    page_obj, extras = _apply_catalog_filters(request, base_qs)

    categories = Category.objects.filter(is_active=True).order_by('name')

    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'category_param': category_param,
        **extras,
        'per_options': PER_OPTIONS,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'category'),
        slug=slug, is_active=True
    )
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
