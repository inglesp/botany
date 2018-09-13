import sys

from django.core.management import BaseCommand

from ... import actions


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("name")

    def handle(self, *args, name, **kwargs):
        print("Paste code below:")
        print("~~~~~~~~~~~~~~~~~")
        print()

        code = sys.stdin.read()

        bot = actions.create_house_bot(name, code)
        print(f"Created bot {bot.id}")
