import importlib.util
from os.path import exists, isdir, join
from os import listdir, makedirs
import sys

import click
import xdg.BaseDirectory

from .db import Database, DatabaseLoader


def ensure_dir(path):
    if not exists(path):
        makedirs(path)


class DatabaseParamType(click.ParamType):
    name = 'database'

    def __init__(self, loader):
        super(DatabaseParamType, self).__init__()
        self.loader = loader

    def convert(self, value, param, ctx):
        exp_type = DatabaseLoader if self.loader else Database
        if isinstance(value, exp_type):
            return value
        try:
            cfg = ctx.find_object(Config)
            loader = cfg.database_loader(value)
            if self.loader:
                return loader
            else:
                return loader.database()
        except Exception as e:
            self.fail("Failed to open database '{}': {}".format(value, e))

DATABASE_LOADER = DatabaseParamType(True)
DATABASE = DatabaseParamType(False)


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

    def default_database_name(self):
        dbs = self.databases()
        if len(dbs) == 1:
            return dbs[0]
        return None

    def database_loader(self, name):
        assert name in self.databases()
        return DatabaseLoader(name, join(self.db_path, name))

    def database(self, name):
        return self.database_loader(name).database()

    def db_argument(self, argname='db', loader=False):
        kind = DATABASE_LOADER if loader else DATABASE
        def decorator(fn):
            return click.argument(argname, type=kind, default=self.default_database_name())(fn)
        return decorator


cfg = Config()
