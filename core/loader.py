# TODO:
#
# * Validate playing modules
# * Validate game module

from importlib import import_module
from types import ModuleType


def create_module_from_str(name, code):
    mod = ModuleType(name)
    exec(code, mod.__dict__)
    return mod


def load_module_from_path(path):
    return import_module(path)
