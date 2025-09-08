from decimal import Decimal


def mini_bag(request):
    """
    Nav dropdown + badge data for the bag.
    """
    bag = request.session.get('bag', {}) or {}

    FREE_DELIVERY_THRESHOLD = Decimal('50.00')
    DELIVERY_FLAT = Decimal('4.99')
    try:
        from checkout.models import FREE_DELIVERY_THRESHOLD as FDT, DELIVERY_FLAT as DF
        FREE_DELIVERY_THRESHOLD, DELIVERY_FLAT = FDT, DF
    except Exception:
        pass

    if not bag:
        return {
            'mini_bag_items': [],
            'bag_item_count': 0,
            'bag_order_total': Decimal('0.00'),
            'bag_delivery_cost': Decimal('0.00'),
            'bag_grand_total': Decimal('0.00'),
            'bag_remaining_to_free': Decimal('0.00'),
            'free_threshold': FREE_DELIVERY_THRESHOLD,
        }

    # Lazy import to avoid circulars
    from products.models import Product

    product_ids = [int(pid) for pid in bag.keys()]
    qs = (Product.objects.filter(id__in=product_ids)
          .select_related('category')
          .prefetch_related('images'))
    products = {p.id: p for p in qs}

    items = []
    order_total = Decimal('0.00')
    item_count = 0

    for pid_str, qty in bag.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(qty)
        price = getattr(product, 'price', Decimal('0.00')) or Decimal('0.00')
        line_total = price * qty
        order_total += line_total
        item_count += qty

        thumb_url = ""
        try:
            imgs = list(product.images.all())
            primary = next(
                (im for im in imgs if getattr(im, 'is_primary', False)),
                imgs[0] if imgs else None
            )
            thumb_url = primary.image.url if primary else ""
        except Exception:
            pass

        items.append({
            'product': product,
            'name': getattr(product, 'name', str(product)),
            'slug': getattr(product, 'slug', ""),
            'qty': qty,
            'price': price,
            'line_total': line_total,
            'thumb_url': thumb_url,
        })

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

    return {
        'mini_bag_items': items,
        'bag_item_count': item_count,
        'bag_order_total': order_total,
        'bag_delivery_cost': delivery_cost,
        'bag_grand_total': grand_total,
        'bag_remaining_to_free': remaining_to_free,
        'free_threshold': FREE_DELIVERY_THRESHOLD,
    }
