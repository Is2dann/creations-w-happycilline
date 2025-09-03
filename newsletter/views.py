import os, requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect

#  From Mailchimp, just leave it here now and change keys when needed.

@require_POST
def subscribe(request):
    email = request.POST.get("email")
    if not email: return redirect("/")  # simple fallback
    api_key = os.getenv("MC_API_KEY", "")
    dc = os.getenv("MC_DC", "")
    list_id = os.getenv("MC_AUDIENCE_ID", "")
    if not (api_key and dc and list_id):  # dev fallback
        request.session["subscribed"] = True
        return redirect("/")
    r = request.post(
        f'https://{dc}.api.mailchimp.com/3.0/lists/{list_id}/members',
        auth=("anystring", api_key),
        json={"email_address": email, "status": "pending"}
    )
    return redirect("/")