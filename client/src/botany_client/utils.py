import json
from functools import lru_cache

import click

from botany_core import loader, verifier

SETTINGS_FILENAME = "botany-settings.json"


@lru_cache()
def read_settings():
    try:
        with open(SETTINGS_FILENAME) as f:
            return json.load(f)
    except FileNotFoundError:
        raise click.UsageError(f"Could not open {SETTINGS_FILENAME}")
    except json.decoder.JSONDecodeError:
        raise click.UsageError(f"{SETTINGS_FILENAME} does not contain valid JSON")


def get_setting(key):
    settings = read_settings()

    try:
        return settings[key]
    except KeyError:
        raise click.UsageError(f"{SETTINGS_FILENAME} does not contain {key}")


def write_settings(settings):
    with open(SETTINGS_FILENAME, "w") as f:
        json.dump(settings, f, indent=4)


def read_bot_code(path):
    try:
        with open(path) as f:
            bot_code = f.read()
    except FileNotFoundError:
        raise click.UsageError(f"Could not read bot code from {path}")

    try:
        verifier.verify_bot_code(bot_code)
    except verifier.InvalidBotCode as e:
        msg = f"""
Bot code at {path} does not conform to the bot specification:

  {e}

Refer to the Botany User Guide for more details
        """.strip()
        raise click.UsageError(msg)

    return bot_code


def create_bot_module(name, path):
    bot_code = read_bot_code(path)
    return loader.create_module_from_str(name, bot_code)


def load_game_module():
    game_module_name = get_setting("botany_game_module")
    try:
        return loader.load_module_from_dotted_path(game_module_name)
    except ModuleNotFoundError:
        msg = f"""
Could not import {game_module_name}

* Have you installed {get_setting('botany_game_package')}?
* Have you activated your virtualenvironment?
        """.strip()
        raise click.UsageError(msg)
