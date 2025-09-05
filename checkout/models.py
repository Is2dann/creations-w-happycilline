import uuid
from decimal import Decimal
from django.db import models
from django_countries.fields import CountryField
from products.models import Product

FREE_DELIVERY_THRESHOLD = Decimal('50.00')
DELIVERY_FLAT = Decimal('4.99')

# These models are generally from the boutique ado project,
# but all of them are tweaked for my purpose


class Order(models.Model):
    order_number = models.CharField(
        max_length=20, unique=True, editable=False, null=False)
    full_name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(max_length=250, null=False, blank=False)
    phone_number = models.CharField(max_length=20, null=False, blank=False)
    address1 = models.CharField(max_length=80, null=False, blank=False)
    address2 = models.CharField(max_length=80, null=True, blank=True)
    city = models.CharField(max_length=50, null=False, blank=False)
    county = models.CharField(max_length=50, null=True, blank=True)
    postcode = models.CharField(max_length=20, null=False, blank=False)
    country = CountryField(
        blank_label=' Select Country', null=False, blank=False)

    date = models.DateTimeField(auto_now_add=True)

    delivery_cost = models.DecimalField(
        max_digits=6, decimal_places=2, default=0)
    order_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    original_bag = models.TextField(blank=False, null=False, default='')
    stripe_pid = models.CharField(
        max_length=250, blank=False, null=False, default='')

    def _generate_order_number(self):
        return uuid.uuid4().hex.upper()

    def update_totals(self):
        self.order_total = sum(
            item.lineitem_total for item in self.lineitems.all()) or Decimal('0.00')
        if self.order_total >= FREE_DELIVERY_THRESHOLD:
            self.delivery_cost = Decimal('0.00')
        else:
            self.delivery_cost = DELIVERY_FLAT if self.order_total > 0 else Decimal('0.00')
        self.grand_total = self.order_total + self.delivery_cost
        self.save(
            update_fields=['order_total', 'delivery_cost', 'grand_total',])

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderLineItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='lineitems', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    lineitem_total = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        price = getattr(
            self.product, 'price', Decimal('0.00')) or Decimal('0.00')
        self.lineitem_total = price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product} x {self.quantity}'
