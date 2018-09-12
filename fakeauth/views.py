from django.conf import settings
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse

from botany.models import User


def authorize(request):
    ix = User.objects.count()
    data = {"name": f"user-{ix}", "email_addr": f"user-{ix}@example.com"}
    signed_data = signing.dumps(data, key=settings.AUTH_SECRET_KEY)

    url = reverse("login", kwargs={"signed_data": signed_data})

    if "next" in request.GET:
        url += f"?next={request.GET['next']}"

    return redirect(url)
