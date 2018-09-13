from django.conf import settings

from botany_core import loader, runner

from . import scheduler
from .models import Bot, Game, User
from .tournament import all_unplayed_games, unplayed_games_for_bot


def create_user(email_addr, name):
    return User.objects.create_user(email_addr=email_addr, name=name)


def deactivate_user(user):
    user.deactivate()
    user.bots.update(state="inactive")


def create_house_bot(name, code):
    # This assertion could be removed if house bots were included in
    # unplayed_games_for_bot().
    assert Bot.objects.exclude(state="house").count() == 0

    bot = Bot.objects.create(name=name, code=code, state="house")
    return bot


def create_bot(user, name, code):
    # TODO add suffix to name
    bot = Bot.objects.create(user=user, name=name, code=code, state="probation")
    schedule_games_against_house_bots(bot)
    return bot


def set_bot_active(bot):
    assert bot.is_under_probation or bot.is_inactive
    bot.set_active()
    schedule_unplayed_games_for_bot(bot)


def mark_bot_failed(bot):
    assert bot.is_under_probation
    bot.set_failed()


def schedule_games_against_house_bots(bot):
    assert bot.is_under_probation
    scheduler.schedule_games_against_house_bots(bot)


def schedule_unplayed_games_for_bot(bot):
    assert bot.is_active
    scheduler.schedule_games(unplayed_games_for_bot(bot))


def schedule_all_unplayed_games():
    scheduler.schedule_games(all_unplayed_games())


def play_games_against_house_bots(bot_id):
    bot = Bot.objects.get(id=bot_id)

    assert bot.is_under_probation

    house_bots = Bot.objects.house_bots()
    for house_bot in house_bots:
        for _ in range(settings.BOTANY_NUM_ROUNDS):
            for bot1_id, bot2_id in [[bot.id, house_bot.id], [house_bot.id, bot.id]]:
                result = play_game(bot1_id, bot2_id)
                report_result(bot1_id, bot2_id, result)

                if not result.is_complete:
                    mark_bot_failed(bot)
                    return

    set_bot_active(bot)


def play_game_and_report_result(bot1_id, bot2_id):
    result = play_game(bot1_id, bot2_id)

    # TODO: schedule this to be run by separate worker to minimise chance of race condition
    report_result(bot1_id, bot2_id, result)


def play_game(bot1_id, bot2_id):
    # TODO: check whether there have been enough reported games between bots
    # TODO: run game in subprocess and ensure environment variables are not accessible
    game = loader.load_module_from_dotted_path(settings.BOTANY_GAME_MODULE)

    bot1 = Bot.objects.get(id=bot1_id)
    bot2 = Bot.objects.get(id=bot2_id)

    mod1 = loader.create_module_from_str("mod1", bot1.code)
    mod2 = loader.create_module_from_str("mod2", bot2.code)

    return runner.run_game(game, mod1.get_next_move, mod2.get_next_move)


def report_result(bot1_id, bot2_id, result):
    # TODO: check whether there have been enough reported games between bots
    # TODO: if game not complete, record reason
    moves = "".join(str(move) for move in result.move_list)
    Game.objects.create(
        bot1_id=bot1_id, bot2_id=bot2_id, score=result.score, moves=moves
    )
