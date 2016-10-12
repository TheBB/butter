import click
from . import cfg
from .gui import run_gui


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Extensible image database tool."""
    ctx.obj = cfg
    if ctx.invoked_subcommand is None:
        ctx.invoke(gui)

cfg.add_commands(main)

@main.command('list')
def list_dbs():
    """Show a list of databases."""
    for db in cfg.databases():
        print(db)

@main.command()
@cfg.db_argument()
def status(db):
    """Show basic information about a database."""
    print(db)

@main.command()
@cfg.db_argument()
def gui(db):
    """Launch the GUI."""
    run_gui(db=db)

@main.command()
@cfg.db_argument(loader=True)
def sync(db):
    db.sync(True)


if __name__ == '__main__':
    main()
