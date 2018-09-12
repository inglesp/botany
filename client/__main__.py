# TODO port to use Click
import os
import sys

import requests

from core import loader, runner

USAGE = """
python -m botany init HOST
python -m botany submit PATH
python -m botany play [PATH,human] [PATH,human]
python -m botany tournament PATH PATH ...
""".strip()


SETTINGS_TPL = """
# TODO Comment this

HOST = "{host}"
API_TOKEN = "{api_token}"
GAME_MODULE = "{botany_game_module}"
NUM_ROUNDS = {botany_num_rounds}
""".lstrip()


def print_usage_and_quit():
    print(USAGE)
    sys.exit(1)


def main(args):
    if not args:
        print_usage_and_quit()

    elif args[0] in ["help", "--help"]:
        print_usage_and_quit()

    elif args[0] == "init":
        if len(args) == 2:
            init(args[1])
        else:
            print_usage_and_quit()

    elif args[0] == "submit":
        if len(args) == 2:
            submit(args[1])
        else:
            print_usage_and_quit()

    elif args[0] == "play":
        if len(args) == 3:
            play(*args[1:])
        else:
            print_usage_and_quit()

    elif args[0] == "tournament":
        if len(args) >= 3:
            tournament(*args[1:])
        else:
            print_usage_and_quit()

    else:
        print_usage_and_quit()


def init(host):
    if host[-1] == "/":
        host = host[:-1]

    setup_url = host + "/api/setup/"
    # TODO If settings.py in current directory, quit
    rsp = requests.get(setup_url)
    data = rsp.json()
    # TODO Check return code

    token_url = host + "/token/"
    print(f"Visit {token_url} and enter your API token")
    api_token = input("> ")

    data["host"] = host
    data["api_token"] = api_token

    with open("settings.py", "w") as f:
        f.write(SETTINGS_TPL.format(**data))


def submit(path):
    import settings

    submit_url = settings.HOST + "/api/submit/"
    bot_name = os.path.basename(path)
    with open(path) as f:
        bot_code = f.read()

    data = {"api_token": settings.API_TOKEN, "bot_name": bot_name, "bot_code": bot_code}
    rsp = requests.post(submit_url, data=data)
    rsp.raise_for_status()


def play(path1, path2):
    import settings

    game = loader.load_module_from_dotted_path(settings.GAME_MODULE)

    def get_next_move_human(board):
        available_moves = game.available_moves(board)

        while True:
            col = input("> ")
            try:
                col = int(col)
            except ValueError:
                continue

            if col not in available_moves:
                continue

            return col

    def wrap_bot_fn(fn):
        param_list = runner.get_param_list(fn)

        def wrapped(board, move_list, token, state):
            input()

            all_args = {
                "board": board,
                "move_list": move_list,
                "token": token,
                "state": state,
            }

            args = {
                param: value for param, value in all_args.items() if param in param_list
            }

            return fn(**args)

        return wrapped

    if path1 == "human":
        fn1 = get_next_move_human
    else:
        mod1 = loader.load_module_from_filesystem_path("mod1", path1)
        fn1 = wrap_bot_fn(mod1.get_next_move)

    if path2 == "human":
        fn2 = get_next_move_human
    else:
        mod2 = loader.load_module_from_filesystem_path("mod2", path2)
        fn2 = wrap_bot_fn(mod2.get_next_move)

    result = runner.run_game(game, fn1, fn2, display_board=True)
    if result.traceback:
        print(result.traceback)


def tournament(*paths):
    # TODO
    assert False


if __name__ == "__main__":
    main(sys.argv[1:])