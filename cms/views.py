from django.shortcuts import render


def delivery(request):
    return render(request, "cms/delivery.html")


def terms_returns(request):
    return render(request, "cms/terms_returns.html")


def faqs(request):
    return render(request, "cms/faq.html")
