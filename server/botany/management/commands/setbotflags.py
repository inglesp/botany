from django.core.management import BaseCommand
from django.db import transaction

from ...models import Bot


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            for bot in Bot.objects.active_bots():
                print(f"{bot.user_name()} :: {bot.name_and_version()}")
                bot.set_flags_etc()
