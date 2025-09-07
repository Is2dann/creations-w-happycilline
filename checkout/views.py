import stripe
import json
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from products.models import Product
from bag.views import _get_bag
from .forms import OrderForm
from .models import Order, OrderLineItem, FREE_DELIVERY_THRESHOLD, DELIVERY_FLAT


def _bag_summary(request):
    """ Compute items and total from the session bag """
    bag = _get_bag(request.session)
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
    remaining_to_free = (
        FREE_DELIVERY_THRESHOLD - order_total) if order_total < FREE_DELIVERY_THRESHOLD else Decimal('0.00')

    return bag, items, order_total, delivery_cost, grand_total, remaining_to_free


@require_http_methods(['GET'])
def checkout(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    bag, items, order_total, delivery_cost, grand_total, remaining_to_free = _bag_summary(request)

    if not bag:
        messages.info(request, 'Your bag is empty.')
        return redirect('bag:view_bag')

    # Creating a payment intent for the current amount
    amount = int(grand_total * settings.STRIPE_PRICE_MULTIPLIER)
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=settings.STRIPE_CURRENCY,
        automatic_payment_methods={'enabled': True},
        metadata={
            'session_key': request.session.session_key or '',
        }
    )

    # If logged in prefill form from profile if have.
    initial = {}
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        initial = {
            'phone_number': profile.phone_number,
            'address1': profile.address1,
            'address2': profile.address2,
            'city': profile.city,
            'county': profile.county,
            'postcode': profile.postcode,
            'country': getattr(profile, 'country', ''),
        }

    form = OrderForm(initial=initial)

    context = {
        'form': form,
        'items': items,
        'order_total': order_total,
        'delivery_cost': delivery_cost,
        'grand_total': grand_total,
        'free_threshold': FREE_DELIVERY_THRESHOLD,
        'remaining_to_free': remaining_to_free,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': intent.client_secret,
    }
    return render(request, 'checkout/checkout.html', context)


# before confirming payment this called by JavaScript
@require_http_methods(['POST'])
def cache_checkout_data(request):
    """
    keeps checkout form data to
    the session so we can create the order after
    payment succeeds
    """
    data = request.POST
    # simple data, no secrets
    request.session['checkout_data'] = {
         'full_name': data.get('full_name', ''),
         'email': data.get('email', ''),
         'phone_number': data.get('phone_number', ''),
         'address1': data.get('address1', ''),
         'address2': data.get('address2', ''),
         'city': data.get('city', ''),
         'county': data.get('county', ''),
         'postcode': data.get('postcode', ''),
         'country': data.get('country', ''),
         'save_info': bool(data.get('save_info', '')),
    }
    return render(request, 'checkout/cache_ok.html')  # empty 200 template


@require_http_methods(['GET'])
def checkout_paid(request):
    client_secret = request.GET.get('payment_intent_client_secret')
    if not client_secret:
        messages.error(request, 'Missing payment client secret.')
        return redirect('checkout:checkout')

    # Retrieve the payment intent and verify payment status
    try:
        pi = stripe.PaymentIntent.retrieve(client_secret.split('_secret')[0])
    except Exception:
        messages.error(request, 'Could not verify payment.')
        return redirect('checkout:checkout')

    if pi.status != 'succeeded':
        messages.error(
            request, 'Your payment was not completed. Please try again.')
        return redirect('checkout:checkout')

    # Builds the order from session data and bag
    bag, items, order_total, delivery_cost, grand_total, _ = _bag_summary(request)
    data = request.session.get('checkout_data', {})
    if not bag or not data:
        messages.error(request, 'Checkout session expired. Please try again.')
        return redirect('bag:view_bag')

    # Creating the order
    order = Order.objects.create(
        full_name=data.get('full_name', ''),
        email=data.get('email', ''),
        phone_number=data.get('phone_number', ''),
        address1=data.get('address1', ''),
        address2=data.get('address2', ''),
        city=data.get('city', ''),
        county=data.get('county', ''),
        postcode=data.get('postcode', ''),
        country=data.get('country', ''),
        order_total=order_total,
        delivery_cost=delivery_cost,
        grand_total=grand_total,
        original_bag=json.dumps(bag),
        stripe_pid=pi.id,
        user_profile=getattr(
            request.user, 'userprofile', None) if request.user.is_authenticated else None,
    )

    #  Line items
    for item in items:
        OrderLineItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['qty'],
        )

        # Save to profile if checkbox is ticked
        if request.user.is_authenticated and data.get('save_info'):
            p = request.user.userprofile
            p.phone_number = data.get('phone_number', p.phone_number)
            p.address1 = data.get('address1', p.address1)
            p.address2 = data.get('address2', p.address2)
            p.city = data.get('city', p.city)
            p.county = data.get('county', p.county)
            p.postcode = data.get('postcode', p.postcode)
            p.country = data.get('country', p.country)
            p.save()

        # clear session bits
        request.session['bag'] = {}
        request.session.pop('checkout_data', None)

        messages.success(
            request, f'Payment received. Your order number is {
                order.order_number}.'
        )
        return redirect(
            'checkout:checkout_success', order_number=order.order_number)


def checkout_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'checkout/checkout_success.html', {'order': order})
