from django.contrib import admin
from .models import Order, OrderLineItem


class OrderLineItemInLine(admin.TabularInline):
    model = OrderLineItem
    readonly_fields = ('lineitem_total',)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'date', 'full_name',
        'order_total', 'delivery_cost', 'grand_total')
    readonly_fields = (
        'order_number', 'date', 'order_total',
        'delivery_cost', 'grand_total', 'original_bag', 'stripe_pid')
    search_fields = ('order_number', 'date', 'full_name')
    inlines = [OrderLineItemInLine]


admin.site.register(OrderLineItem)
