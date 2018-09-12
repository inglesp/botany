import django_rq
from django.conf import settings

from . import actions


def schedule_games_against_house_bots(bot):
    queue = get_house_queue()

    if settings.USE_QUEUES:
        queue.enqueue(actions.play_games_against_house_bots, bot.id)


def schedule_games(unplayed_games):
    """Schedule unplayed games.

    unplayed_games is a dict mapping (bot1_id, bot2_id) to the number of games
    that have not yet been played between bot1 and bot2.

    settings.USE_QUEUES is usually False in tests, which speeds up tests
    (especially those using Hypothesis) significantly.
    """
    queue = get_main_queue()

    for (bot1_id, bot2_id), num_games in unplayed_games.items():
        assert 0 < num_games <= settings.BOTANY_NUM_ROUNDS

        for ix in range(num_games):
            if settings.USE_QUEUES:
                queue.enqueue(actions.play_game_and_report_result, bot1_id, bot2_id)


def get_house_queue():
    return django_rq.get_queue("house")


def get_main_queue():
    return django_rq.get_queue("main")


def clear_queues():
    for queue_name in settings.RQ_QUEUES:
        queue = django_rq.get_queue(queue_name)
        queue.empty()
