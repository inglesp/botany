from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from . import managers


class AbastractBotanyModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, AbastractBotanyModel):
    email_addr = models.EmailField("email address", unique=True)
    name = models.CharField(max_length=200)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    api_token = models.CharField(max_length=12, unique=True)

    objects = managers.UserManager()

    USERNAME_FIELD = "email_addr"
    EMAIL_FIELD = "email_addr"
    REQUIRED_FIELDS = ["name"]

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def deactivate(self):
        self.is_active = False
        self.save()

    @property
    def active_bot(self):
        try:
            return self.bots.get(is_active=True)
        except Bot.DoesNotExist:
            return None


class Bot(AbastractBotanyModel):
    user = models.ForeignKey(User, related_name="bots", on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    code = models.TextField()
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def set_public(self):
        self.is_public = True
        self.save()

    def set_not_public(self):
        self.is_public = False
        self.save()

    def set_active(self):
        self.user.bots.update(is_active=False)
        self.is_active = True
        self.save()

    @property
    def score(self):
        bot1_games_score = self.bot1_games.aggregate(score=models.Sum("result"))[
            "score"
        ]
        bot2_games_score = self.bot2_games.aggregate(score=models.Sum("result"))[
            "score"
        ]

        return bot1_games_score - bot2_games_score


class Game(AbastractBotanyModel):
    bot1 = models.ForeignKey(Bot, related_name="bot1_games", on_delete=models.CASCADE)
    bot2 = models.ForeignKey(Bot, related_name="bot2_games", on_delete=models.CASCADE)
    result = models.IntegerField()
