import json

from botany_core import loader


def load_settings():
    # TODO Could raise file not found
    with open("botany-settings.json") as f:
        # TODO Could raise JSON decoding error
        return json.load(f)


def load_game():
    settings = load_settings()
    # TODO Could raise KeyError
    game_module = settings["botany_game_module"]
    # TODO Could raise import error
    return loader.load_module_from_dotted_path(game_module)
