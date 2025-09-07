from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('paid/', views.checkout_paid, name='checkout_paid'),
    path('cache/', views.cache_checkout_data, name='cache_checkout_data'),
    path('wh/', views.stripe_webhook, name='stripe_webhook'),
    path('success/<order_number>/', views.checkout_success, name='checkout_success'),
]
