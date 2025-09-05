import json
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from products.models import Product
from bag.views import _get_bag
from .forms import OrderForm
from .models import Order, OrderLineItem, FREE_DELIVERY_THRESHOLD, DELIVERY_FLAT


@require_http_methods(['GET', 'POST'])
def checkout(request):
    bag = _get_bag(request.session)

    if not bag:
        messages.info(request, 'Your bag is empty.')
        return redirect('bag:view_bag')

    # A bag summary for the template
    product_ids = [int(pid) for pid in bag.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    items = []
    order_total = Decimal('0.00')

    for pid_str, qty in bag.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        price = getattr(product, 'price', Decimal('0.00')) or Decimal('0.00')
        line_total = price * qty
        order_total += line_total
        items.append({
            'product': product,
            'qty': qty,
            'line_total': line_total
        })

    delivery_cost = Decimal(
        '0.00') if order_total >= FREE_DELIVERY_THRESHOLD else (
            DELIVERY_FLAT if order_total > 0 else Decimal('0.00')
        )
    grand_total = order_total + delivery_cost

    if order_total < FREE_DELIVERY_THRESHOLD:
        remaining_to_free = FREE_DELIVERY_THRESHOLD - order_total
    else:
        remaining_to_free = Decimal('0.00')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.original_bag = json.dumps(bag)
            order.save()
            for item in items:
                OrderLineItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['qty'],
                )
            order.update_totals()
            request.session['bag'] = {}

            messages.success(
                request, f'Order placed! Your order number is {
                    order.order_number}.')
            return redirect(
                'checkout:checkout_success', order_number=order.order_number)
        else:
            messages.error(
                request, 'There was an error with your form. Please review and try again.')
    else:
        form = OrderForm()

    context = {
        'form': form,
        'items': items,
        'order_total': order_total,
        'delivery_cost': delivery_cost,
        'grand_total': grand_total,
        'free_threshold': FREE_DELIVERY_THRESHOLD,
        'remaining_to_free': remaining_to_free,
    }
    return render(request, 'checkout/checkout.html', context)


def checkout_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'checkout/checkout_success.html', {'order': order})
