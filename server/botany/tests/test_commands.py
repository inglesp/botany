import os

from django.core.management import call_command
from django.test import TestCase

from botany.models import User


class CreatesuperuserTests(TestCase):
    def test_createsuperuser(self):
        with open(os.devnull, "w") as f:
            call_command(
                "createsuperuser",
                interactive=False,
                email_addr="alice@example.com",
                name="Alice Apple",
                stdout=f,
            )

        user = User.objects.get(email_addr="alice@example.com")

        self.assertEqual(user.name, "Alice Apple")
        self.assertEqual(len(user.api_token), 12)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_superuser)
