"""
URL configuration for cwh_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('home.urls')),
    path('about/', include('about.urls')),
    path('products/', include(('products.urls', 'products'), namespace='products')),
    path('bag/', include('bag.urls', namespace='bag')),
    # path('checkout/', include(('checkout.urls', 'checkout'), namespace='checkout')),
    # # path('profile/', include(('profiles.urls', 'profiles'), namespace='profiles')),
    path('cms/', include('cms.urls')),  # Just leave it here for now as planned privacy and faqs on separate pages
    # path('newsletter/', include('newsletter.urls')),  # Newsletter is not wired up yet
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# handler404 = 'cwh_site.views.handler404'  # for later use
