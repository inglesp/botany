from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.crypto import get_random_string


class UserManager(BaseUserManager):
    def _create_user(
        self, email_addr, name, password=None, is_admin=False, is_superuser=False
    ):
        if not email_addr:
            raise ValueError("email_addr must be set")
        email_addr = self.normalize_email(email_addr)
        user = self.model(
            email_addr=email_addr,
            name=name,
            is_admin=is_admin,
            is_superuser=is_superuser,
            api_token=get_random_string(12),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email_addr, name):
        return self._create_user(email_addr, name)

    def create_superuser(self, email_addr, name, password):
        return self._create_user(
            email_addr=email_addr,
            name=name,
            password=password,
            is_admin=True,
            is_superuser=True,
        )


class BotManager(models.Manager):
    def active_bots(self):
        return self.filter(is_active=True)


class GameManager(models.Manager):
    def games_between_active_bots(self):
        return self.filter(bot1__is_active=True, bot2__is_active=True)
