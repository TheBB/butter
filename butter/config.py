import click
import os
import os.path as path
from xdg import XDG_CONFIG_HOME

import butter.plugin as plugin


root_path = str(XDG_CONFIG_HOME / 'butter')
data_path = path.join(root_path, 'databases')
plugin_path = path.join(root_path, 'plugins')

databases = sorted(os.listdir(data_path))
try:
    default_database = databases[0]
except IndexError:
    default_database = None
