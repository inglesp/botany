from botany_core import loader, runner
from django.conf import settings
from django.db import transaction

from . import scheduler
from .models import Bot, Game, User
from .tournament import all_unplayed_games, unplayed_games_for_bot


def create_user(email_addr, name):
    assert name != "house"
    return User.objects.create_user(email_addr=email_addr, name=name)


def deactivate_user(user):
    user.deactivate()
    user.bots.update(state="inactive")


def set_beginner_flag(user, is_beginner):
    user.is_beginner = is_beginner
    user.save()


def create_house_bot(name, code):
    # This assertion could be removed if house bots were included in
    # unplayed_games_for_bot().
    assert Bot.objects.exclude(state="house").count() == 0

    bot = Bot.objects.create(name=name, version=0, code=code, state="house")
    return bot


def create_bot(user, name, code):
    version = user.bots.filter(name=name).count()
    bot = Bot.objects.create(
        user=user, name=name, version=version, code=code, state="probation"
    )
    schedule_games_against_house_bots(bot)
    return bot


def set_bot_active(bot, user):
    assert bot.is_under_probation or bot.is_inactive
    assert bot.user == user
    user.bots.active_bots().update(state="inactive")
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


def play_games_between_house_bots():
    assert Game.objects.count() == 0

    house_bots = Bot.objects.house_bots()

    with transaction.atomic():
        for bot1 in house_bots:
            for bot2 in house_bots:
                if bot1 == bot2:
                    continue

                for _ in range(settings.BOTANY_NUM_ROUNDS):
                    result = play_game(bot1.id, bot2.id)
                    assert result.is_complete
                    report_result(bot1.id, bot2.id, result)


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

    set_bot_active(bot, bot.user)


def play_game_and_report_result(bot1_id, bot2_id):
    result = play_game(bot1_id, bot2_id)

    report_result(bot1_id, bot2_id, result)


def play_game(bot1_id, bot2_id):
    if (
        Game.objects.filter(bot1_id=bot1_id, bot2_id=bot2_id).count()
        == settings.BOTANY_NUM_ROUNDS
    ):
        return

    # TODO: run game in subprocess and ensure environment variables are not accessible
    game = loader.load_module_from_dotted_path(settings.BOTANY_GAME_MODULE)

    bot1 = Bot.objects.get(id=bot1_id)
    bot2 = Bot.objects.get(id=bot2_id)

    if bot1.is_inactive or bot2.is_inactive:
        return

    mod1 = loader.create_module_from_str("mod1", bot1.code)
    mod2 = loader.create_module_from_str("mod2", bot2.code)

    return runner.run_game(
        game,
        mod1.get_next_move,
        mod2.get_next_move,
        opcode_limit=settings.BOTANY_OPCODE_LIMIT,
    )


def report_result(bot1_id, bot2_id, result):
    if (
        Game.objects.filter(bot1_id=bot1_id, bot2_id=bot2_id).count()
        == settings.BOTANY_NUM_ROUNDS
    ):
        return

    moves = "".join(str(move) for move in result.move_list)
    Game.objects.create(
        bot1_id=bot1_id,
        bot2_id=bot2_id,
        score=result.score,
        moves=moves,
        result_type=result.result_type.value,
        traceback=result.traceback,
    )
