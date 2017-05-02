from contextlib import contextmanager
import importlib.util
from os.path import exists, isdir, join
from os import listdir, makedirs
import sys

import click
import xdg.BaseDirectory

import butter.db as db


def ensure_dir(path):
    if not exists(path):
        makedirs(path)


class DatabaseParamType(click.ParamType):
    name = 'database'

    def __init__(self):
        super(DatabaseParamType, self).__init__()

    def convert(self, value, param, ctx):
        if isinstance(value, db.loader_class):
            return value
        try:
            cfg = ctx.find_object(MasterConfig)
            return cfg.database_loader(value)
        except Exception as e:
            self.fail("Failed to open database '{}': {}".format(value, e))

DATABASE_LOADER = DatabaseParamType()


class MasterConfig:

    def __init__(self):
        self.config_path = xdg.BaseDirectory.save_config_path('butter')

        self.plugin_path = join(self.config_path, 'plugins')
        ensure_dir(self.plugin_path)
        sys.path.append(self.plugin_path)
        self.loaded_plugins = set()
        self.load_plugins = True

        self.db_path = join(self.config_path, 'databases')
        ensure_dir(self.db_path)

    def load_plugin(self, name, main=None):
        if name in self.loaded_plugins or not self.load_plugins:
            return
        path = join(self.plugin_path, name)
        if isdir(path):
            try:
                spec = importlib.util.spec_from_file_location(name, join(path, '__init__.py'))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'enable'):
                    module.enable()
                self.loaded_plugins.add(name)
            except Exception as e:
                print("Failed to load plugin '{}': {}".format(name, e), file=sys.stderr)

    def plugin_loaded(self, name):
        return name in self.loaded_plugins

    def databases(self):
        return sorted(listdir(self.db_path))

    def default_database_name(self):
        dbs = self.databases()
        if len(dbs) == 1:
            return dbs[0]
        return None

    def database_loader(self, name):
        assert name in self.databases()
        loader = db.loader_class(name, join(self.db_path, name))
        for plugin in loader.plugins:
            self.load_plugin(plugin)
        return db.loader_class(name, join(self.db_path, name))

    @contextmanager
    def database(self, name, *args, **kwargs):
        with self.database_loader(name).database(*args, **kwargs) as db:
            yield db
            db.close()

    def db_argument(self, argname='db'):
        def decorator(fn):
            return click.argument(argname, type=DATABASE_LOADER,
                                  default=self.default_database_name())(fn)
        return decorator

cfg = MasterConfig()
