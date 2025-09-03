from django.contrib import admin
from .models import Profile, Address


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'marketing_opt_in', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'label', 'city',
        'postcode', 'country',
        'is_default_shipping', 'is_default_billing')
    list_filter = ('country', 'is_default_shipping', 'is_default_billing')
    search_fields = ('user__username', 'user__email', 'city', 'postcode')
