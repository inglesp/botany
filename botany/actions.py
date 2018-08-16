from .models import Bot, Game, User


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
    # TODO
    pass


def schedule_all_unplayed_games():
    # TODO
    pass


def play_game(bot1_id, bot2_id):
    # TODO
    pass


def report_result(bot1_id, bot2_id, score):
    # TODO: check whether there have been enough reported games between bots
    # TODO: store list of moves
    Game.objects.create(bot1_id=bot1_id, bot2_id=bot2_id, score=score)
