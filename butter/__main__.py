import click
import functools

from butter.gui import run_gui
import butter.config as config
from butter.db import DatabaseLoader


class DatabaseLoaderType(click.ParamType):
    name = 'database'

    def __init__(self):
        super().__init__()

    def convert(self, value, param, ctx):
        if isinstance(value, DatabaseLoader):
            return value
        try:
            return DatabaseLoader(value)
        except Exception as e:
            self.fail(f"Failed to open database: '{value}': {e}")

db_argument = functools.partial(
    click.argument, type=DatabaseLoaderType(), default=config.default_database
)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Extensible image database."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(gui)


@main.command('list')
def list_dbs():
    """Show a list of databases."""
    for db in config.databases:
        print(db)


@main.command()
@db_argument('loader')
def status(loader):
    """Show basic information about a database."""
    with loader.database() as db:
        print(db)


@main.command()
@db_argument('loader')
def gui(loader):
    """Launch the GUI."""
    with loader.database() as db:
       run_gui(db=db)


@main.command()
@click.option('--push/--no-push', default=True)
@click.option('--pull/--no-pull', default=True)
@click.option('--stage/--no-stage', default=True)
@click.option('-v', '--verbose', default=False, is_flag=True)
@db_argument('loader')
def sync(loader, **kwargs):
    """Synchronize a database."""
    loader.sync(**kwargs)


if __name__ == '__main__':
    main()
