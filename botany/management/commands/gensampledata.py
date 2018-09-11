import random

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction
from django.test import override_settings

from botany.tests import factories

from ... import actions


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            with override_settings(USE_QUEUES=False):
                for _ in range(4):
                    factories.create_house_bot()
                bots = [factories.create_bot(state="probation") for _ in range(20)]

            for bot1 in bots:
                actions.play_games_against_house_bots(bot1.id)

                for bot2 in bots:
                    if bot1 == bot2:
                        continue

                    for _ in range(random.randint(0, settings.BOTANY_NUM_ROUNDS)):
                        result = actions.play_game(bot1.id, bot2.id)
                        actions.report_result(bot1.id, bot2.id, result)
