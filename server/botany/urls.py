from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("winners/", views.winners, name="winners"),
    path("standings/", views.full_standings, name="full_standings"),
    path("bots/<bot_id>/", views.bot, name="bot"),
    path("bots/<bot_id>/standings/", views.bot_standings, name="bot_standings"),
    path("bots/<bot_id>/games/", views.bot_games, name="bot_games"),
    path(
        "bots/<bot_id>/games/<other_bot_id>/",
        views.bot_head_to_head,
        name="bot_head_to_head",
    ),
    path("download-bots/", views.download_bots_code, name="download_bots_code"),
    path("users/<user_id>/", views.user, name="user"),
    path("users/<user_id>/bots/", views.user_bots, name="user_bots"),
    path("games/<game_id>/", views.game, name="game"),
    path("play/<bot1_id>/<bot2_id>/", views.play, name="play"),
    path("login/", views.prelogin, name="prelogin"),
    path("login/<signed_data>/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("token/", views.token, name="token"),
    path("api/setup/", views.api_setup, name="api_setup"),
    path("api/submit/", views.api_submit, name="api_submit"),
    path(
        "api/download-bots/",
        views.api_download_bots_code,
        name="api_download_bots_code"
    ),
    path("500/", views.error),
]


if settings.USE_FAKE_AUTH:
    from fakeauth.views import authorize

    urlpatterns.append(path("fakeauth/authorize/", authorize))
