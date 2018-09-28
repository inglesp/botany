import os.path as op
from functools import lru_cache

from botany_core.runner import Result, ResultType

from botany import actions

user_ix = 0
bot_ix = 0


def create_user(email_addr=None, name=None, num_bots=0):
    global user_ix
    user_ix += 1

    email_addr = email_addr or f"alice-{user_ix}@example.com"
    name = name or f"Alice Apple {user_ix}"

    user = actions.create_user(email_addr, name)

    for _ in range(num_bots):
        create_bot(user)

    return user


def create_house_bot(name=None, code=None):
    global bot_ix
    bot_ix += 1

    name = name or f"bot-{bot_ix}"
    code = code or bot_code("randobot")

    return actions.create_house_bot(name, code)


def create_bot(user=None, name=None, code=None, state="active"):
    global bot_ix
    bot_ix += 1

    user = user or create_user()
    name = name or f"bot-{bot_ix}"
    code = code or bot_code("randobot")

    bot = actions.create_bot(user, name, code)

    if state == "probation":
        pass
    elif state == "active":
        actions.set_bot_active(bot, user)
    else:
        assert False

    return bot


@lru_cache()
def bot_code(bot_name):
    path = op.join(op.dirname(op.abspath(__file__)), "bots", bot_name + ".py")
    with open(path) as f:
        return f.read()


def report_result(bot1_id, bot2_id, score, move_list=None):
    if move_list is None:
        move_list = []

    result = Result(
        result_type=ResultType.COMPLETE,
        score=score,
        move_list=move_list,
        traceback=None,
        invalid_move=None,
    )

    actions.report_result(bot1_id, bot2_id, result)
