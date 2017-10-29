import click
import os
import os.path as path
import xdg.BaseDirectory as xdg
import yapsy.PluginManager as yapsy

import butter.plugin as plugin


root_path = xdg.save_config_path('butter')
data_path = path.join(root_path, 'databases')
plugin_path = path.join(root_path, 'plugins')

databases = sorted(os.listdir(data_path))
try:
    default_database = databases[0]
except IndexError:
    default_database = None


class PluginManager(yapsy.PluginManager):

    def __init__(self, loader):
        super().__init__(categories_filter={
            'all': plugin.PluginBase,
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
        obj = self._plugins[name] = self.activatePluginByName(name, 'all')
        obj.manager = self
        for cmd in obj.commands:
            self._commands[cmd.name] = cmd

    def list_commands(self):
        return list(self._commands.keys())

    def command(self, name):
        return self._commands[name]
