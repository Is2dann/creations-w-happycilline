from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from .models import Category, Product, Wishlist, ProductReview
from .forms import ProductForm, ProductReviewForm, ProductImageFormSet

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
            product_count=Count(
                "product",
                filter=Q(product__is_active=True),
            )
        )
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
        slug=slug,
        is_active=True,
    )
    # This picks primary image or first as fallback
    primary = product.images.filter(
        is_primary=True,
    ).first() or product.images.first()
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

    # Wishlist info
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product,
        ).exists()

    # Reviews + average rating
    reviews = product.reviews.filter(approved=True)
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg']

    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'primary_image': primary,
        'gallery': gallery,
        'gallery_js': gallery_js,
        'in_wishlist': in_wishlist,
        'reviews': reviews,
        'average_rating': average_rating,
        'user_review': user_review,
    })


# -------------------------------------------------------------------
# Admin-only Product CRUD views (UI-based)
# -------------------------------------------------------------------


def _is_staff_user(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(_is_staff_user)
def admin_product_list(request):
    """
    Admin-facing list of all products, with search, filters,
    thumbnail and links to edit/delete.
    """
    products = (
        Product.objects.all()
        .select_related('category')
        .prefetch_related('images')
    )

    # Search by name/description/SKU
    q = (request.GET.get("q") or "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(sku__icontains=q)
        )

    # Filter by category (id)
    raw_category = (request.GET.get("category") or "").strip()
    category_id = None
    if raw_category:
        try:
            category_id = int(raw_category)
            products = products.filter(category_id=category_id)
        except ValueError:
            category_id = None

    # Filter by active status
    active_param = (request.GET.get("active") or "").strip()
    if active_param == "1":
        products = products.filter(is_active=True)
    elif active_param == "0":
        products = products.filter(is_active=False)

    products = products.order_by("name")
    categories = Category.objects.filter(is_active=True).order_by("name")

    return render(request, 'products/admin/product_admin_list.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'category_id': category_id,
        'active_param': active_param,
    })


@login_required
@user_passes_test(_is_staff_user)
def product_create(request):
    """
    Create a new product via the UI, including images.
    Staff/superusers only.
    """
    product = Product()

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(
            request.POST,
            request.FILES,
            instance=product,
        )

        if form.is_valid() and formset.is_valid():
            product = form.save()
            # instance already bound; just save related images
            formset.save()
            messages.success(
                request,
                f'Product "{product.name}" created successfully.',
            )
            return redirect("products:admin_product_list")
    else:
        form = ProductForm()
        formset = ProductImageFormSet(instance=product)

    return render(
        request,
        "products/admin/product_form.html",
        {
            "form": form,
            "formset": formset,
            "title": "Add Product",
            "submit_label": "Create Product",
        },
    )


@login_required
@user_passes_test(_is_staff_user)
def product_update(request, pk):
    """
    Update an existing product, including its images.
    Staff/superusers only.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(
            request.POST,
            request.FILES,
            instance=product,
        )

        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.save()
            messages.success(
                request,
                f'Product "{product.name}" updated successfully.',
            )
            return redirect("products:admin_product_list")
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)

    return render(
        request,
        "products/admin/product_form.html",
        {
            "form": form,
            "formset": formset,
            "title": "Edit Product",
            "submit_label": "Save Changes",
            "product": product,
        },
    )


@login_required
@user_passes_test(_is_staff_user)
def product_delete(request, pk):
    """
    Delete a product after confirmation.
    Staff/superusers only.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(
            request,
            f'Product "{name}" deleted successfully.',
        )
        return redirect('products:admin_product_list')

    return render(request, 'products/admin/product_confirm_delete.html', {
        'product': product,
    })


# -------------------------------------------------------------------
# Wishlist views
# -------------------------------------------------------------------


@login_required
def wishlist_list(request):
    """
    Show the logged-in user's wishlist items.
    """
    items = (
        Wishlist.objects.filter(user=request.user)
        .select_related('product', 'product__category')
        .order_by('-created_at')
    )
    return render(request, 'products/wishlist.html', {
        'items': items,
    })


@login_required
def wishlist_toggle(request, product_id):
    """
    Toggle product in the user's wishlist.
    POST only.
    """
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    wishlist_qs = Wishlist.objects.filter(
        user=request.user,
        product=product,
    )

    if wishlist_qs.exists():
        wishlist_qs.delete()
        messages.info(
            request,
            f'"{product.name}" removed from your wishlist.',
        )
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(
            request,
            f'"{product.name}" added to your wishlist.',
        )

    redirect_url = request.POST.get('redirect_url')
    if redirect_url:
        return redirect(redirect_url)
    return redirect('products:detail', slug=product.slug)


# -------------------------------------------------------------------
# Product review views
# -------------------------------------------------------------------


@login_required
def product_review(request, slug):
    """
    Create or update the logged-in user's review for a product.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    # Get existing review by this user if it exists
    existing_review = ProductReview.objects.filter(
        product=product,
        user=request.user,
    ).first()

    if request.method == "POST":
        form = ProductReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            if existing_review:
                messages.success(
                    request,
                    'Your review has been updated.',
                )
            else:
                messages.success(
                    request,
                    'Thank you for reviewing this product!',
                )
            return redirect('products:detail', slug=product.slug)
    else:
        form = ProductReviewForm(instance=existing_review)

    return render(request, 'products/product_review_form.html', {
        'product': product,
        'form': form,
        'existing_review': existing_review,
    })
