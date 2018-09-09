from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("standings/", views.full_standings, name="full_standings"),
    path("bots/<bot_id>/", views.bot, name="bot"),
    path("bots/<bot_id>/standings/", views.bot_standings, name="bot_standings"),
    path("bots/<bot_id>/games/", views.bot_games, name="bot_games"),
    path(
        "bots/<bot_id>/games/<other_bot_id>/",
        views.bot_head_to_head,
        name="bot_head_to_head",
    ),
    path("games/<game_id>/", views.game, name="game"),
]
