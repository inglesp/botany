from django.core.management import BaseCommand

from ... import actions


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        actions.play_games_between_house_bots()
