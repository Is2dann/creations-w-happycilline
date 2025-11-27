from django.conf import settings
from django.db import models
from django.utils.text import slugify


RATING_CHOICES = [(i, i) for i in range(1, 6)]


class Category(models.Model):

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=275, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(
        'Category', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    sku = models.CharField(max_length=6, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(null=True, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'sort_order', 'id']

    def __str__(self):
        return f'{self.product.name} image #{self.pk}'
    

class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.product}'
    

class ProductReview(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=100, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return (
            f'Review {self.rating}/5 on {self.product} by '
            f'{self.user}'
        )
