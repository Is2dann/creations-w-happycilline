from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_order_confirmation(order):
    ctx = {
        'order': order,
        'items': order.lineitems.select_related('product').all()
    }
    subject = render_to_string(
        'emails/order_confirmation_subject.txt', ctx).strip()
    text = render_to_string('emails/order_confirmation.txt', ctx)
    html = render_to_string('emails/order_confirmation.html', ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
        bcc=[
            settings.SHOP_OWNER_EMAIL] if getattr(
                settings, 'SHOP_OWNER_EMAIL', '') else None,
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
