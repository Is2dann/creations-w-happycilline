# checkout/views.py
import json
import time
import logging
logger = logging.getLogger(__name__)
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bag.views import _get_bag
from products.models import Product
from profiles.models import UserProfile
from .emails import send_order_confirmation
from .forms import OrderForm
from .models import (
    FREE_DELIVERY_THRESHOLD,
    DELIVERY_FLAT,
    Order,
    OrderLineItem,
)

# ---------- Helpers ----------


def _bag_summary(request):
    """ Counts items and totals from the session bag. """
    bag = _get_bag(request.session)
    product_ids = [int(pid) for pid in bag.keys()]
    products = {
        p.id: p for p in Product.objects.filter(id__in=product_ids)
    }

    items = []
    order_total = Decimal('0.00')

    for pid_str, qty in bag.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        price = getattr(
            product, 'price', Decimal('0.00')) or Decimal('0.00')
        line_total = price * qty
        order_total += line_total
        items.append(
            {
                'product': product,
                'qty': qty,
                'line_total': line_total
            }
        )

    delivery_cost = (
        Decimal('0.00')
        if order_total >= FREE_DELIVERY_THRESHOLD
        else (DELIVERY_FLAT if order_total > 0 else Decimal('0.00'))
    )
    grand_total = order_total + delivery_cost
    remaining_to_free = (
        FREE_DELIVERY_THRESHOLD - order_total
        if order_total < FREE_DELIVERY_THRESHOLD
        else Decimal('0.00')
    )
    return bag, items, order_total, delivery_cost, grand_total, remaining_to_free


def _summary_from_bag_dict(bag_dict):
    """ Counts items/totals from a plain dict. """
    product_ids = [int(pid) for pid in bag_dict.keys()]
    products = {
        p.id: p for p in Product.objects.filter(id__in=product_ids)
    }

    items = []
    order_total = Decimal('0.00')

    for pid_str, qty in bag_dict.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        price = getattr(
            product, 'price', Decimal('0.00')) or Decimal('0.00')
        line_total = price * qty
        order_total += line_total
        items.append(
            {
                'product': product,
                'qty': qty,
                'line_total': line_total
            }
        )

    delivery_cost = (
        Decimal('0.00')
        if order_total >= FREE_DELIVERY_THRESHOLD
        else (DELIVERY_FLAT if order_total > 0 else Decimal('0.00'))
    )
    grand_total = order_total + delivery_cost
    return items, order_total, delivery_cost, grand_total


# ---------- Views ----------

@require_http_methods(["GET"])
def checkout(request):
    """
    Render checkout with stripe payment intent and payment element.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    bag, items, order_total, delivery_cost, grand_total, remaining_to_free = _bag_summary(request)
    if not bag:
        messages.info(request, "Your bag is empty.")
        return redirect('bag:view_bag')

    # Create a payment intent
    amount = int(
        grand_total * int(getattr(settings, 'STRIPE_PRICE_MULTIPLIER', 100))
    )
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=getattr(settings, 'STRIPE_CURRENCY', 'gbp'),
        automatic_payment_methods={"enabled": True},
        metadata={"session_key": request.session.session_key or ''},
    )

    # Prefill from profile
    initial = {}
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        p = request.user.userprofile
        initial = {
            'phone_number': p.phone_number,
            'address1': p.address1,
            'address2': p.address2,
            'city': p.city,
            'county': p.county,
            'postcode': p.postcode,
            'country': getattr(p, 'country', ''),
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


@require_http_methods(["POST"])
def cache_checkout_data(request):
    """
    Saves checkout form to session and
    attaches minimal data to the payment intent
    metadata so the webhook can build the order without the browser returning.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    data = request.POST

    # Session (used by return-url path as a fallback)
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
        'save_info': bool(data.get('save_info')),
    }

    # Attach to payment intent metadata for webhook flow
    client_secret = data.get('client_secret')
    if client_secret:
        intent_id = client_secret.split('_secret')[0]
        bag = _get_bag(request.session)
        meta = {
            'bag': json.dumps(bag),
            'full_name': data.get('full_name', ''),
            'email': data.get('email', ''),
            'phone_number': data.get('phone_number', ''),
            'address1': data.get('address1', ''),
            'address2': data.get('address2', ''),
            'city': data.get('city', ''),
            'county': data.get('county', ''),
            'postcode': data.get('postcode', ''),
            'country': data.get('country', ''),
            'save_info': 'true' if data.get('save_info') else 'false',
            'user_id': str(getattr(request.user, 'id', '')),
            'profile_id': str(
                getattr(getattr(
                    request.user, 'userprofile', None
                ), 'id', '')
            ),
        }
        try:
            stripe.PaymentIntent.modify(intent_id, metadata=meta)
        except Exception:
            # don't block checkout if metadata update fails
            pass

    return render(request, 'checkout/cache_ok.html')  # tiny 200 template


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Create the Order on payment_intent.succeeded.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    wh_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.warning("Stripe webhook signature/payload error: %s", e)
        return HttpResponse(status=400)

    if event['type'] != 'payment_intent.succeeded':
        return HttpResponse(status=200)

    pi = event['data']['object']
    stripe_pid = pi['id']
    metadata = pi.get('metadata', {}) or {}

    # Idempotency: bail if already created
    if Order.objects.filter(stripe_pid=stripe_pid).exists():
        return HttpResponse(status=200)

    try:
        # Build from metadata
        try:
            bag = json.loads(metadata.get('bag', '{}'))
        except Exception:
            bag = {}
        items, order_total, delivery_cost, grand_total = _summary_from_bag_dict(bag)

        user_profile = None
        profile_id = metadata.get('profile_id')
        if profile_id:
            try:
                user_profile = UserProfile.objects.get(id=profile_id)
            except UserProfile.DoesNotExist:
                user_profile = None

        order = Order.objects.create(
            full_name=metadata.get('full_name', ''),
            email=metadata.get('email', ''),
            phone_number=metadata.get('phone_number', ''),
            address1=metadata.get('address1', ''),
            address2=metadata.get('address2', ''),
            city=metadata.get('city', ''),
            county=metadata.get('county', ''),
            postcode=metadata.get('postcode', ''),
            country=metadata.get('country', ''),
            order_total=order_total,
            delivery_cost=delivery_cost,
            grand_total=grand_total,
            original_bag=json.dumps(bag),
            stripe_pid=stripe_pid,
            user_profile=user_profile,
        )
        for item in items:
            OrderLineItem.objects.create(
                order=order, product=item['product'], quantity=item['qty']
            )

        if user_profile and metadata.get('save_info') == 'true':
            p = user_profile
            p.phone_number = metadata.get('phone_number', p.phone_number)
            p.address1 = metadata.get('address1', p.address1)
            p.address2 = metadata.get('address2', p.address2)
            p.city = metadata.get('city', p.city)
            p.county = metadata.get('county', p.county)
            p.postcode = metadata.get('postcode', p.postcode)
            p.country = metadata.get('country', p.country)
            p.save()

        
        try:
            send_order_confirmation(order)
        except Exception as e:
            logger.info(
                "Order %s created; email failed: %s", order.order_number, e)

        logger.info(
            "Order %s created by webhook for %s",
            order.order_number, stripe_pid
        )
        return HttpResponse(status=200)

    except Exception as e:
        # Log full traceback but don't loop 500s forever
        logger.exception("Webhook failed for %s: %s", stripe_pid, e)
        # Returning 200 stops Stripe from endlessly retrying
        return HttpResponse(status=200)


@require_http_methods(["GET"])
def checkout_paid(request):
    """
    - If webhook already created the order, redirect to success.
    - Otherwise wait briefly; if still not found,
        create it here from PI metadata/session.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    client_secret = request.GET.get('payment_intent_client_secret')
    if not client_secret:
        messages.error(request, "Missing payment client secret.")
        return redirect('checkout:checkout')

    pi_id = client_secret.split('_secret')[0]
    try:
        pi = stripe.PaymentIntent.retrieve(pi_id)
    except Exception:
        messages.error(request, "Could not verify payment.")
        return redirect('checkout:checkout')

    if pi.status != 'succeeded':
        messages.error(
            request, "Your payment was not completed. Please try again."
        )
        return redirect('checkout:checkout')

    # 1) Try to find order created by webhook
    for _ in range(5):
        existing = Order.objects.filter(stripe_pid=pi.id).first()
        if existing:
            messages.success(
                request,
                f"Payment received. Your order number is {
                    existing.order_number}."
            )
            request.session['bag'] = {}
            request.session.pop('checkout_data', None)
            return redirect(
                'checkout:checkout_success',
                order_number=existing.order_number
            )
        time.sleep(1)

    # 2) Fallback: build and create here
    meta = getattr(pi, 'metadata', {}) or {}
    try:
        bag_from_meta = json.loads(meta.get('bag', '{}'))
    except Exception:
        bag_from_meta = {}

    if bag_from_meta:
        # Use metadata (preferred)
        items, order_total, delivery_cost, grand_total = _summary_from_bag_dict(
            bag_from_meta
        )
        user_profile = None
        profile_id = meta.get('profile_id')
        if profile_id:
            try:
                user_profile = UserProfile.objects.get(id=profile_id)
            except UserProfile.DoesNotExist:
                pass

        order, created = Order.objects.get_or_create(
            stripe_pid=pi.id,
            defaults=dict(
                full_name=meta.get('full_name', ''),
                email=meta.get('email', ''),
                phone_number=meta.get('phone_number', ''),
                address1=meta.get('address1', ''),
                address2=meta.get('address2', ''),
                city=meta.get('city', ''),
                county=meta.get('county', ''),
                postcode=meta.get('postcode', ''),
                country=meta.get('country', ''),
                order_total=order_total,
                delivery_cost=delivery_cost,
                grand_total=grand_total,
                original_bag=json.dumps(bag_from_meta),
                user_profile=user_profile,
            ),
        )
        if created:
            for item in items:
                OrderLineItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['qty']
                )
    else:
        # Last fallback
        bag, items, order_total, delivery_cost, grand_total, _ = _bag_summary(
            request
        )
        data = request.session.get('checkout_data', {})
        if not bag or not data:
            messages.info(
                request,
                "Payment received. We're finalising your order;" \
                "it will appear in your profile shortly."
            )
            request.session['bag'] = {}
            request.session.pop('checkout_data', None)
            return redirect('profiles:profile')

        order, created = Order.objects.get_or_create(
            stripe_pid=pi.id,
            defaults=dict(
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
                user_profile=getattr(
                    request.user, 'userprofile', None) if request.user.is_authenticated else None,
            ),
        )
        if created:
            for item in items:
                OrderLineItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['qty']
                )

    request.session['bag'] = {}
    request.session.pop('checkout_data', None)
    messages.success(
        request,
        f"Payment received. Your order number is {order.order_number}."
    )
    return redirect(
        'checkout:checkout_success', order_number=order.order_number)


def checkout_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'checkout/checkout_success.html', {'order': order})
