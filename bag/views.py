from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from products.models import Product


def _get_bag(session):
    bag = session.get('bag', {})
    if not isinstance(bag, dict):
        bag = {}
    return bag


def view_bag(request):
    bag = _get_bag(request.session)
    items = []
    product_ids = [int(pid) for pid in bag.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    subtotal = Decimal('0.00')
    total_qty = 0
    for pid_str, qty in bag.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        line_total = (product.price or 0) * qty
        subtotal += line_total
        total_qty += qty
        items.append({
            'product': product,
            'qty': qty,
            'line_total': line_total,
        })
    
    context = {
        'items': items,
        'total_qty': total_qty,
        'subtotal': subtotal,
    }
    return render(request, 'bag/bag.html', context)


@require_POST
def add_to_bag(request, item_id):
    product = get_object_or_404(Product, pk=item_id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1

    bag = _get_bag(request.session)
    key = str(product.id)
    bag[key] = bag.get(key, 0) + qty
    request.session['bag'] = bag

    messages.success(request, f'Added {qty} x {product.name} to your shopping bag.')

    # Redirect back to the page we came from (code from Stackoverflow (tweaked))
    redirect_url = request.POST.get('redirect_url') or request.META.get('HTTP_REFERER') or 'bag:view_bag'
    return redirect(redirect_url)


@require_POST
def adjust_bag(request, item_id):
    product = get_object_or_404(Product, pk=item_id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    bag = _get_bag(request.session)
    key = str(product.id)

    if qty > 0:
        bag[key] = qty
        messages.info(request, f'Updated {product.name} quantity to {qty}.')
    else:
        removed = bag.pop(key, None)
        if removed:
            messages.info(request, f'Removed {qty} x {product.name} from your shopping bag.')

    request.session['bag'] = bag
    return redirect('bag:view_bag')


@require_POST
def remove_from_bag(request, item_id):
    product = get_object_or_404(Product, pk=item_id)
    bag = _get_bag(request.session)
    key = str(product.id)

    if key in bag:
        bag.pop(key)
        messages.warning(request, f'Removed {product.name} from your shopping bag.')
        request.session['bag'] = bag

    return redirect('bag:view_bag')
