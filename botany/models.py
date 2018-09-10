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
    is_active = models.BooleanField(default=False)

    objects = managers.BotManager()

    def __init__(self, *args, **kwargs):
        self._score = None
        self._num_played = None
        self._num_wins = None
        self._num_draws = None
        self._num_losses = None
        super().__init__(*args, **kwargs)

    def set_active(self):
        self.user.bots.update(is_active=False)
        self.is_active = True
        self.save()

    @property
    def score(self):
        if self._score is None:
            bot1_games_score = (
                self.bot1_games.aggregate(score=models.Sum("score"))["score"] or 0
            )
            bot2_games_score = (
                self.bot2_games.aggregate(score=models.Sum("score"))["score"] or 0
            )
            self._score = bot1_games_score - bot2_games_score
        return self._score

    @score.setter
    def score(self, score):
        self._score = score

    @property
    def num_played(self):
        if self._num_played is None:
            bot1_games_num_played = self.bot1_games.count()
            bot2_games_num_played = self.bot2_games.count()
            self._num_played = bot1_games_num_played + bot2_games_num_played
        return self._num_played

    @num_played.setter
    def num_played(self, num_played):
        self._num_played = num_played

    @property
    def num_wins(self):
        if self._num_wins is None:
            bot1_games_num_wins = self.bot1_games.filter(score=1).count()
            bot2_games_num_wins = self.bot2_games.filter(score=-1).count()
            self._num_wins = bot1_games_num_wins + bot2_games_num_wins
        return self._num_wins

    @num_wins.setter
    def num_wins(self, num_wins):
        self._num_wins = num_wins

    @property
    def num_draws(self):
        if self._num_draws is None:
            bot1_games_num_draws = self.bot1_games.filter(score=0).count()
            bot2_games_num_draws = self.bot2_games.filter(score=0).count()
            self._num_draws = bot1_games_num_draws + bot2_games_num_draws
        return self._num_draws

    @num_draws.setter
    def num_draws(self, num_draws):
        self._num_draws = num_draws

    @property
    def num_losses(self):
        if self._num_losses is None:
            bot1_games_num_losses = self.bot1_games.filter(score=-1).count()
            bot2_games_num_losses = self.bot2_games.filter(score=1).count()
            self._num_losses = bot1_games_num_losses + bot2_games_num_losses
        return self._num_losses

    @num_losses.setter
    def num_losses(self, num_losses):
        self._num_losses = num_losses


class Game(AbastractBotanyModel):
    bot1 = models.ForeignKey(Bot, related_name="bot1_games", on_delete=models.CASCADE)
    bot2 = models.ForeignKey(Bot, related_name="bot2_games", on_delete=models.CASCADE)
    score = models.IntegerField()
    moves = models.CharField(max_length=255)

    objects = managers.GameManager()

    def summary(self):
        if self.score == 1:
            return f"{self.bot1.name} won"
        elif self.score == 0:
            return "draw"
        elif self.score == -1:
            return f"{self.bot2.name} won"
        else:
            assert False

    def move_list(self):
        return [int(s) for s in self.moves]
