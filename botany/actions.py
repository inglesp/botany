from django.conf import settings

from core import loader, runner

from .models import Bot, Game, User
from .scheduler import schedule_games
from .tournament import all_unplayed_games, unplayed_games_for_bot


def create_user(email_addr, name):
    return User.objects.create_user(email_addr=email_addr, name=name)


def deactivate_user(user):
    user.deactivate()
    user.bots.update(is_active=False)


def create_bot(user, name, code, is_public):
    bot = Bot.objects.create(user=user, name=name, code=code, is_public=is_public)
    set_bot_active(bot)
    return bot


def set_bot_public(bot):
    bot.set_public()


def set_bot_not_public(bot):
    bot.set_not_public()


def set_bot_active(bot):
    bot.set_active()
    schedule_unplayed_games_for_bot(bot)


def schedule_unplayed_games_for_bot(bot):
    schedule_games(unplayed_games_for_bot(bot))


def schedule_all_unplayed_games():
    schedule_games(all_unplayed_games())


def play_game(bot1_id, bot2_id):
    # TODO: check whether there have been enough reported games between bots
    # TODO: run game in subprocess and ensure environment variables are not accessible
    game = loader.load_module_from_path(settings.BOTANY_GAME_MODULE)

    bot1 = Bot.objects.get(id=bot1_id)
    bot2 = Bot.objects.get(id=bot2_id)

    mod1 = loader.create_module_from_str("mod1", bot1.code)
    mod2 = loader.create_module_from_str("mod2", bot2.code)

    result = runner.run_game(game, mod1.get_next_move, mod2.get_next_move)

    # TODO: schedule this to be run by separate worker to minimise chance of race condition
    report_result(bot1_id, bot2_id, result)


def report_result(bot1_id, bot2_id, result):
    # TODO: check whether there have been enough reported games between bots
    moves = "".join(str(move) for move in result.move_list)
    Game.objects.create(
        bot1_id=bot1_id, bot2_id=bot2_id, score=result.score, moves=moves
    )
