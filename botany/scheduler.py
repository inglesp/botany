import django_rq
from django.conf import settings

from . import actions


def schedule_games(unplayed_games):
    """Schedule unplayed games.

    unplayed_games is a dict mapping (bot1_id, bot2_id) to the number of games
    that have not yet been played between bot1 and bot2.

    There are BOTANY_NUM_ROUNDS queues, and we schedule at most one game
    between bot1 and bot2 on each queue.

    settings.USE_QUEUES is usually False in tests, which speeds up tests
    (especially those using Hypothesis) significantly.
    """
    for (bot1_id, bot2_id), num_games in unplayed_games.items():
        assert 0 < num_games <= settings.BOTANY_NUM_ROUNDS

        for ix in range(num_games):
            queue_name = settings.QUEUE_NAMES[ix]

            if settings.USE_QUEUES:
                queue = django_rq.get_queue(queue_name)
                queue.enqueue(actions.play_game, bot1_id, bot2_id)


def get_queue_by_ix(ix):
    return django_rq.get_queue(settings.QUEUE_NAMES[ix])


def clear_queues():
    for ix in range(settings.BOTANY_NUM_ROUNDS):
        queue_name = settings.QUEUE_NAMES[ix]
        queue = django_rq.get_queue(queue_name)
        queue.empty()
