from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist


def _render_first(paths, ctx):
    for p in paths:
        try:
            return render_to_string(p, ctx)
        except TemplateDoesNotExist:
            continue
    return None


def send_order_confirmation(order):
    ctx = {
        "order": order,
        "items": order.lineitems.select_related("product").all()
    }

    subject = (
        _render_first(
            ["emails/order_confirmation_subject.txt",
             "checkout/emails/order_confirmation_subject.txt",
             ], ctx
        ) or f"Your order {order.order_number} confirmation"
    ).strip()

    text = (
        _render_first(
            ["emails/order_confirmation.txt",
             "checkout/emails/order_confirmation.txt",
             ], ctx
        ) or (
            "Hi {name}\n\nThanks for your order {num}.\nTotal: £{tot:.2f}\n".format(
                name=order.full_name,
                num=order.order_number,
                tot=order.grand_total)
            )
    )

    html = _render_first(
        ["emails/order_confirmation.html",
         "checkout/emails/order_confirmation.html",
         ], ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
        bcc=(
            [settings.SHOP_OWNER_EMAIL] if getattr(
                settings, "SHOP_OWNER_EMAIL", "") else None),
    )
    if html:
        msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
