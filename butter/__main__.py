import click
from . import cfg


@click.group()
@click.pass_context
def main(ctx):
    """Extensible image database tool."""
    ctx.obj = cfg

cfg.add_commands(main)

@main.command('list')
def list_dbs():
    """Show a list of databases."""
    for db in cfg.databases():
        print(db)

@main.command('status')
@cfg.db_argument()
def status(db):
    """Show basic information about a database."""
    print(db)


if __name__ == '__main__':
    main()
