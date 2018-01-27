import click
import functools
import sys

from butter.gui import run_gui
import butter.config as config
from butter.plugin import db_argument, default_loader


class PluginCommands(click.MultiCommand):

    def list_commands(self, ctx):
        db = default_loader()
        if db is None:
            return []
        return db.plugin_manager.list_commands()

    def get_command(self, ctx, name):
        db = default_loader()
        return db.plugin_manager.command(name)

plugin_cmds = PluginCommands()


@click.group()
def builtin_cmds():
    """Extensible image database."""
    pass


@builtin_cmds.command('list')
def list_dbs():
    """Show a list of databases."""
    for db in config.databases:
        print(db)


@builtin_cmds.command()
@db_argument('loader')
def status(loader):
    """Show basic information about a database."""
    with loader.database() as db:
        print(db)


@builtin_cmds.command()
@db_argument('loader')
@click.option('--safe/--no-safe', default=False)
def gui(loader, safe):
    """Launch the GUI."""
    with loader.database() as db:
       run_gui(db=db, safe=safe)


@builtin_cmds.command()
@click.option('--push/--no-push', default=True)
@click.option('--pull/--no-pull', default=True)
@click.option('--stage/--no-stage', default=True)
@click.option('-v', '--verbose', default=False, is_flag=True)
@db_argument('loader')
def sync(loader, **kwargs):
    """Synchronize a database."""
    loader.sync(**kwargs)


@builtin_cmds.command('push-config')
@db_argument('loader')
def push_config(loader):
    """Push config to remote."""
    loader.push_config()


@builtin_cmds.command('pull-config')
@db_argument('loader')
def pull_config(loader):
    """Pull config from remote."""
    loader.pull_config()


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1].startswith('-d'):
            config.default_database = sys.argv[1][2:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]
            assert config.default_database in config.databases
        elif len(sys.argv) > 2 and sys.argv[1] == '--db':
            config.default_database = sys.argv[2]
            sys.argv = [sys.argv[0]] + sys.argv[3:]
            assert config.default_database in config.databases
    except AssertionError:
        print(f"Unknown database: '{config.default_database}'")

    if len(sys.argv) == 1:
        sys.argv.append('gui')

    click.CommandCollection(name='Butter', sources=[builtin_cmds, plugin_cmds])()


if __name__ == '__main__':
    main()
