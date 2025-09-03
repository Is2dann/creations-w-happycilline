from django.conf import settings
from django.db import models
from django_countries.fields import CountryField


User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, null=True, blank=True)
    marketing_opt_in = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile({self.user})'


class Address(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=40, default='Home')
    full_name = models.CharField(max_length=120, null=True, blank=True)
    line1 = models.CharField(max_length=120, null=True, blank=True)
    line2 = models.CharField(max_length=120, null=True, blank=True)
    city = models.CharField(max_length=80, null=True, blank=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    country = CountryField(blank_label='Country', null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default_shipping', '-is_default_billing', 'label']

    def __str__(self):
        return f'{self.label} ({self.user})'
