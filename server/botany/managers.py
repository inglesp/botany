from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.db.models import Q
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
    def house_bots(self):
        return self.filter(state="house")

    def active_bots(self):
        return self.filter(state="active")

    def active_or_house_bots(self):
        return self.filter(state__in=["active", "house"])


class GameManager(models.Manager):
    def games_between_active_bots(self):
        return self.filter(bot1__state="active", bot2__state="active")

    def games_between_active_or_house_bots(self):
        return self.filter(
            bot1__state__in=["active", "house"], bot2__state__in=["active", "house"]
        )

    def all_against_bot(self, bot):
        return self.filter(Q(bot1=bot) | Q(bot2=bot)).order_by("-created_at")

    def all_between_bots(self, bot1, bot2):
        return self.filter(
            (Q(bot1=bot1) & Q(bot2=bot2)) | (Q(bot1=bot2) & Q(bot2=bot1))
        ).order_by("-created_at")

    def recent(self, n):
        return self.order_by("-created_at")[:n]

    def recent_against_bot(self, bot, n):
        return self.filter(Q(bot1=bot) | Q(bot2=bot)).order_by("-created_at")[:n]
