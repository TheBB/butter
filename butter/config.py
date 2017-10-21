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

    def __init__(self):
        super().__init__(categories_filter={
            'all': plugin.PluginBase,
        })
        self.setPluginPlaces([plugin_path])
        self.collectPlugins()

    def activate(self, name):
        self.activatePluginByName(name)
