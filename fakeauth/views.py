from django.conf import settings
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse


def authorize(request):
    name = input("name: ") or "peter"
    email_addr = input("email_addr: ") or "peter@example.com"

    data = {"name": name, "email_addr": email_addr}
    signed_data = signing.dumps(data, key=settings.AUTH_SECRET_KEY)

    url = reverse("login", kwargs={"signed_data": signed_data})

    if "next" in request.GET:
        url += f"?next={request.GET['next']}"

    return redirect(url)
