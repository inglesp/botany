import json
import random
import urllib
from base64 import b64decode, b64encode
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import login, logout
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from botany_core import loader, runner, verifier

from .actions import create_bot, create_user, set_beginner_flag, set_bot_active
from .models import Bot, Game, User
from .tournament import (
    all_games_against_bot,
    all_games_between_bots,
    head_to_head_summary,
    recent_games,
    recent_games_against_bot,
    standings,
    standings_against_bot,
    summary,
)


def index(request):
    top_of_standings = standings()[:10]
    tournament_closed = datetime.now(timezone.utc) > settings.BOTANY_TOURNAMENT_CLOSE_AT

    ctx = {
        "summary": summary(),
        "recent_games": recent_games(),
        "top_of_standings": top_of_standings,
        "tournament_closed": tournament_closed,
    }
    return render(request, "botany/index.html", ctx)


def full_standings(request):
    ctx = {"standings": standings()}
    return render(request, "botany/full_standings.html", ctx)


def bot(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)
    standings = list(standings_against_bot(bot))
    top_of_standings = standings[:5]
    bottom_of_standings = standings[-5:]
    show_code = (
        bot.is_house_bot
        or request.user.is_superuser
        or request.user == bot.user
        or (
            bot.is_active
            and datetime.now(timezone.utc) > settings.BOTANY_TOURNAMENT_CLOSE_AT
        )
    )

    ctx = {
        "bot": bot,
        "recent_games": recent_games_against_bot(bot),
        "top_of_standings": top_of_standings,
        "bottom_of_standings": bottom_of_standings,
        "show_code": show_code,
    }
    return render(request, "botany/bot.html", ctx)


def bot_standings(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)

    ctx = {"bot": bot, "standings": standings_against_bot(bot)}
    return render(request, "botany/bot_standings.html", ctx)


def bot_games(request, bot_id):
    bot = get_object_or_404(Bot, id=bot_id)

    ctx = {"bot": bot, "games": all_games_against_bot(bot)}
    return render(request, "botany/bot_games.html", ctx)


def bot_head_to_head(request, bot_id, other_bot_id):
    bot = get_object_or_404(Bot, id=bot_id)
    other_bot = get_object_or_404(Bot, id=other_bot_id)
    games = all_games_between_bots(bot, other_bot)
    summary = head_to_head_summary(games, bot, other_bot)

    ctx = {"bot": bot, "other_bot": other_bot, "games": games, "summary": summary}
    return render(request, "botany/bot_head_to_head.html", ctx)


def play(request, bot1_id, bot2_id):
    if bot1_id == "human":
        assert bot2_id is not "human"
    else:
        bot = get_object_or_404(Bot, id=bot1_id)
        title = f"human vs {bot.name_and_version()}"

    if bot2_id == "human":
        assert bot1_id is not "human"
    else:
        bot = get_object_or_404(Bot, id=bot2_id)
        title = f"{bot.name_and_version()} vs human"

    game_mod = loader.load_module_from_dotted_path(settings.BOTANY_GAME_MODULE)

    if request.POST:
        moves = request.POST["moves"]
        move_list = [int(m) for m in moves]
        next_move = int(request.POST["next_move"])

        token = game_mod.TOKENS[len(moves) % 2]
        other_token = game_mod.TOKENS[(len(moves) + 1) % 2]

        boards = runner.rerun_game(game_mod, move_list)
        board = boards[-1]
        assert game_mod.is_valid_move(board, next_move)

        game_mod.make_move(board, next_move, token)
        move_list.append(next_move)
        state = None

        if not game_mod.check_winner(board):
            bot_mod = loader.create_module_from_str("bot", bot.code)
            fn = bot_mod.get_next_move
            param_list = runner.get_param_list(fn)
            if "state" in request.POST:
                state = json.loads(b64decode(request.POST["state"]))

            all_args = {
                "board": board,
                "move_list": move_list,
                "token": other_token,
                "state": state,
            }

            args = {
                param: value for param, value in all_args.items() if param in param_list
            }

            rv = fn(**args)
            try:
                next_next_move, state = rv
                print("Got a state")
            except TypeError:
                next_next_move, state = rv, None
                print("Got no state")
            move_list.append(next_next_move)

        moves = "".join(str(m) for m in move_list)

        qs_dict = {"moves": moves}
        if state is not None:
            qs_dict["state"] = b64encode(json.dumps(state).encode("utf8"))

        qs = urllib.parse.urlencode(qs_dict)
        return redirect(reverse("play", args=[bot1_id, bot2_id]) + f"?{qs}")

    if request.GET.get("moves"):
        moves = request.GET["moves"]
        state = request.GET.get("state")
        move_list = [int(m) for m in request.GET["moves"]]
        boards = runner.rerun_game(game_mod, move_list)
        board = boards[-1]

        if game_mod.check_winner(board):
            token = game_mod.TOKENS[(len(moves) + 1) % 2]
            result = f"{token} wins"
        elif len(game_mod.available_moves(board)) == 0:
            result = "draw"
        else:
            result = None
    else:
        moves = ""
        board = game_mod.new_board()
        state = None
        result = None

    ctx = {
        "title": title,
        "result": result,
        "moves": moves,
        "state": state,
        "board": game_mod.render_html(board),
        "styles": game_mod.html_styles,
    }

    return render(request, "botany/play.html", ctx)


def user(request, user_id):
    if request.POST:
        user = get_object_or_404(User, id=user_id)
        editable = user == request.user

        if not editable:
            raise PermissionDenied

        set_beginner_flag(user, request.POST["is_beginner"] == "y")

    return redirect(reverse("user_bots", args=[user_id]))


def user_bots(request, user_id):
    bot_user = get_object_or_404(User, id=user_id)
    tournament_closed = datetime.now(timezone.utc) > settings.BOTANY_TOURNAMENT_CLOSE_AT
    editable = bot_user == request.user and not tournament_closed

    if request.POST:
        if not editable:
            raise PermissionDenied

        bot = get_object_or_404(Bot, id=request.POST["bot_id"])
        set_bot_active(bot, request.user)
        return redirect(reverse("user_bots", args=[user_id]))

    ctx = {
        "bot_user": bot_user,
        "bots": bot_user.bots.order_by("-created_at"),
        "editable": editable,
        "bot_img_src": f"botany/img/botany-bot-{random.randint(1, 7)}.png",
    }
    return render(request, "botany/user_bots.html", ctx)


def game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    game_mod = loader.load_module_from_dotted_path(settings.BOTANY_GAME_MODULE)
    boards = runner.rerun_game(game_mod, game.move_list())

    rendered_boards = [game_mod.render_html(board) for board in boards]

    ctx = {
        "game": game,
        "bot1": game.bot1,
        "bot2": game.bot2,
        "boards": rendered_boards,
        "styles": game_mod.html_styles,
    }
    return render(request, "botany/game.html", ctx)


def prelogin(request):
    url = settings.AUTH_LOGIN_URL
    if "next" in request.GET:
        url += f"?next={request.GET['next']}"
    return redirect(url)


def login_view(request, signed_data):
    data = signing.loads(
        signed_data, key=settings.AUTH_SECRET_KEY, max_age=settings.AUTH_MAX_AGE
    )
    email_addr = data["email_addr"]
    name = data["name"]

    try:
        user = User.objects.get(email_addr=email_addr)
    except User.DoesNotExist:
        user = create_user(email_addr, name)

    login(request, user)

    return redirect(request.GET.get("next", "/"))


def logout_view(request):
    logout(request)

    return redirect("/")


def token(request):
    if request.user.is_authenticated:
        return render(request, "botany/token.html")
    else:
        url = f"{reverse('prelogin')}?next={request.path}"
        return redirect(url)


def api_setup(request):
    data = {
        "botany_game_module": settings.BOTANY_GAME_MODULE,
        "botany_game_package": settings.BOTANY_GAME_PACKAGE,
        "botany_num_rounds": settings.BOTANY_NUM_ROUNDS,
        "botany_opcode_limit": settings.BOTANY_OPCODE_LIMIT,
    }
    return JsonResponse(data)


@csrf_exempt
def api_submit(request):
    if datetime.now(timezone.utc) > settings.BOTANY_TOURNAMENT_CLOSE_AT:
        return HttpResponseBadRequest("Tournament has closed")

    user = get_object_or_404(User, api_token=request.POST["api_token"])

    try:
        bot_code = request.FILES["bot_code"].read().decode("utf8")
    except KeyError:
        bot_code = request.POST["bot_code"]

    try:
        verifier.verify_bot_code(bot_code)
    except verifier.InvalidBotCode as e:
        return HttpResponseBadRequest("Bot code not valid")

    create_bot(user, request.POST["bot_name"], bot_code)
    return JsonResponse({})


def error(request):
    1 / 0
