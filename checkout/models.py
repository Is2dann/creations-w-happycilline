from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING)

    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, default=0)
    shipping = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, default=0)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, default=0)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, default=0)

    # Use string app labels to avoid circular imports across apps
    shipping_address = models.ForeignKey(
        "profiles.Address", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="shipping_orders")
    billing_address = models.ForeignKey(
        "profiles.Address", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="billing_orders")

    payment_intent_id = models.CharField(
        max_length=200, blank=True)  # Stripe linkage

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} - {self.status}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product', on_delete=models.PROTECT,
        related_name='order_items')

    # Snapshots to preserve price/name at purchase time
    product_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
