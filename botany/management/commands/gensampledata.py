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
                bots = [factories.create_bot() for ix in range(20)]

            for bot1 in bots:
                for bot2 in bots:
                    if bot1 == bot2:
                        continue

                    for _ in range(random.randint(0, settings.BOTANY_NUM_ROUNDS)):
                        actions.play_game(bot1.id, bot2.id)
