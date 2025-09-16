from unittest.mock import patch
from decimal import Decimal
from django.test import TestCase, override_settings
from django.core import mail
from django.urls import reverse
from products.models import Product
from checkout.models import Order, OrderLineItem
from checkout.emails import send_order_confirmation


class StripeFlowTests(TestCase):
    @patch('checkout.views.stripe')
    def test_checkout_paid_creates_order(self, mock_stripe):
        # Mock PI retrieve to return succeeded
        mock_stripe.PaymentIntent.retrieve.return_value = type(
            'PI', (), {'id': 'pi_123', 'status': 'succeeded'})
        p = Product.objects.create(name='X', price=Decimal('10.00'))
        s = self.client.session
        s['bag'] = {str(p.id): 2}
        s['checkout_data'] = {
            'full_name': 'A',
            'email': 'a@b.com',
            'phone_number': '1',
            'address1': 'x',
            'address2': '',
            'city': 't',
            'county': '',
            'postcode': 'z',
            'country': 'GB',
            'save_info': False
        }
        s.save()
        r = self.client.get(
            reverse(
                'checkout:checkout_paid'
            ) + '?payment_intent_client_secret=pi_123_secret_abc'
        )
        self.assertEqual(r.status_code, 302)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class EmailTests(TestCase):
    def test_order_mail(self):
        p = Product.objects.create(name='X', price=Decimal('10.00'))
        o = Order.objects.create(
            full_name='T', email='t@t.com', phone_number='1',
            address1='A', city='C', postcode='P', country='GB',
            order_total=Decimal('10.00'), delivery_cost=Decimal('10.00'),
            grand_total=Decimal('10.00')
        )
        OrderLineItem.objects.create(
            order=o, product=p, quantity=1
        )
        send_order_confirmation(o)
        self.assertTrue(mail.outbox)
        self.assertIn(str(o.order_number), mail.outbox[0].subject)
