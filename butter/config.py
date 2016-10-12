import importlib.util
from os.path import exists, isdir, join
from os import listdir, makedirs
import sys

import click
import xdg.BaseDirectory

from .db import Database


def ensure_dir(path):
    if not exists(path):
        makedirs(path)


class DatabaseParamType(click.ParamType):
    name = 'database'

    def convert(self, value, param, ctx):
        if isinstance(value, Database):
            return value
        try:
            cfg = ctx.find_object(Config)
            return cfg.database(value)
        except Exception as e:
            self.fail("Failed to open database '{}': {}".format(value, e))

DATABASE = DatabaseParamType()


class Config:

    def __init__(self):
        self.config_path = xdg.BaseDirectory.save_config_path('butter')

        self.plugin_path = join(self.config_path, 'plugins')
        ensure_dir(self.plugin_path)

        self.db_path = join(self.config_path, 'databases')
        ensure_dir(self.db_path)

    def add_commands(self, main):
        for name in listdir(self.plugin_path):
            path = join(self.plugin_path, name)
            if isdir(path):
                try:
                    spec = importlib.util.spec_from_file_location(name, join(path, '__init__.py'))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'commands'):
                        for cmd in module.commands():
                            main.add_command(cmd)
                except Exception as e:
                    print("Failed to load plugin '{}': {}".format(name, e), file=sys.stderr)

    def databases(self):
        return sorted(listdir(self.db_path))

    def default_database(self):
        dbs = self.databases()
        if len(dbs) == 1:
            return dbs[0]
        return None

    def database(self, name):
        assert name in self.databases()
        return Database(name, join(self.db_path, name))

    def db_argument(self, argname='db'):
        def decorator(fn):
            return click.argument(argname, type=DATABASE, default=self.default_database())(fn)
        return decorator


cfg = Config()
