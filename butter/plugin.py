import functools
from click import command, option, argument

import yapsy.PluginManager as yapsy


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
            loader = default_loader()
            try:
                return func(*args, **kwargs, **{name: loader})
            finally:
                loader.close()
        return inner
    return decorator


class PluginBase:

    commands = []

    def activate(self):
        pass

    def deactivate(self):
        pass

    @property
    def loader(self):
        return self.manager.loader

    def db(self, *args, **kwargs):
        return self.loader.database(*args, **kwargs)


class PluginManager(yapsy.PluginManager):

    def __init__(self, loader):
        from butter.config import plugin_path

        super().__init__(categories_filter={
            'all': PluginBase,
        })
        self._commands = {}
        self.setPluginPlaces([plugin_path])
        self.collectPlugins()

        self._plugins = {}
        self._commands = {}
        self.loader = loader

    def __iter__(self):
        yield from self._plugins.values()

    def __getitem__(self, name):
        return self._plugins[name]

    def activate(self, name):
        if name in self._plugins:
            return
        self.getPluginByName(name, 'all').plugin_object.manager = self
        obj = self._plugins[name] = self.activatePluginByName(name, 'all')
        for cmd in obj.commands:
            self._commands[cmd.name] = cmd

    def deactivate_all(self):
        for obj in self:
            obj.deactivate()

    def list_commands(self):
        return list(self._commands.keys())

    def command(self, name):
        return self._commands[name]


_DISPATCHES = ['add_failed', 'add_succeeded']
_GETTERS = ['get_default_program']

def src_dispatcher(name):
    def inner(self, *args, **kwargs):
        for obj in self:
            getattr(obj, name)(*args, **kwargs)
    return inner

def src_getter(name):
    def inner(self, *args, **kwargs):
        for obj in self:
            ret = getattr(obj, name)(*args, **kwargs)
            if ret:
                return ret
        return None
    return inner

for name in _DISPATCHES:
    setattr(PluginBase, name, lambda *args, **kwargs: None)
    setattr(PluginManager, name, src_dispatcher(name))

for name in _GETTERS:
    setattr(PluginBase, name, lambda *args, **kwargs: None)
    setattr(PluginManager, name, src_getter(name))
