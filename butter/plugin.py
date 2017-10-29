import functools
from click import command, option, argument


def default_loader():
    from butter.config import default_database
    from butter.db import DatabaseLoader
    if default_database is not None:
        return DatabaseLoader(default_database)
    return None


def db_argument(name):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs, **{name: default_loader()})
        return inner
    return decorator


class PluginBase:

    commands = []

    def activate(self):
        pass

    @property
    def loader(self):
        return self.manager.loader
