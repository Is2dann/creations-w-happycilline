from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import UserProfileForm


@login_required
def profile(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profiles:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UserProfileForm(instance=profile)

    orders = getattr(profile, 'orders', None)
    context = {
        'form': form,
        'orders': orders.all().order_by('-date') if orders else [],
    }
    return render(request, 'profiles/profile.html', context)
