from django.urls import path
from . import views

app_name = "policies"

urlpatterns = [
    path("delivery/", views.delivery, name="delivery"),
    path("terms-returns/", views.terms_returns, name="terms"),
    path("faqs/", views.faqs, name="faqs"),
]
