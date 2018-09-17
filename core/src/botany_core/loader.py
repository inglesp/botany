from importlib import import_module
from types import ModuleType


def create_module_from_str(name, code, path=None):
    mod = ModuleType(name)
    if path is not None:
        mod.__file__ = path
        code = compile(code, path, "exec")
    exec(code, mod.__dict__)
    return mod


def load_module_from_dotted_path(path):
    return import_module(path)
