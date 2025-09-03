from django.http import HttpResponse
from django.shortcuts import render


def custom_404(request, exception=None):
    return render(request, "404.html", status=404)


def privacy(request):
    return render(request, "cms/privacy.html")  # Just leave it here in case will need it


def faq(request):
    return render(request, "cms/faq.html")  # Just leave it here in case will need it