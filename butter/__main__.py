import click
import imagehash
import inflect
from itertools import combinations
import multiprocessing
from PIL import Image
from tqdm import tqdm
from . import cfg
from .gui import run_gui
from .programs import Images


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Extensible image database tool."""
    ctx.obj = cfg
    if ctx.invoked_subcommand is None:
        ctx.invoke(gui)

cfg.load_plugins(main)


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
@click.option('--push/--no-push', default=True)
@click.option('--pull/--no-pull', default=True)
@click.option('--stage/--no-stage', default=True)
@click.option('-v', '--verbose', default=False, is_flag=True)
@cfg.db_argument(loader=True)
def sync(db, **kwargs):
    """Synchronize a database."""
    db.sync(**kwargs)


@main.command('push-config')
@cfg.db_argument(loader=True)
def push_config(db):
    """Push config to remote."""
    db.push_config()


@main.command('show-deletes')
@cfg.db_argument()
def show_deletes(db):
    pics = list(db.delete_pics())
    if pics:
        run_gui(program=Images.factory(*pics))


def image_hash(pic_id, pic_filename):
    return (pic_id, imagehash.phash(Image.open(pic_filename)))

def image_diff(a, b):
    pic_a, hash_a = a
    pic_b, hash_b = b
    return (pic_a, pic_b, abs(hash_a - hash_b))

@main.command()
@click.option('--threshold', '-t', type=int, default=9)
@click.option('--nprocs', type=int, default=1)
@click.option('--chunksize', type=int, default=20)
@cfg.db_argument()
def deduplicate(db, threshold, nprocs, chunksize):
    """Find duplicate images."""
    pics = {pic.id: pic.filename for pic in db.query()}
    pool = multiprocessing.Pool(nprocs)
    hashes = pool.starmap(image_hash, tqdm(pics.items(), desc='Computing hashes'),
                          chunksize=chunksize)
    pool.close()

    # Could use multiprocessing here too but it seems communication-dominated
    ndiffs = len(hashes) * (len(hashes) - 1) // 2
    diffs = [(pic_a, pic_b, abs(hash_a - hash_b))
             for (pic_a, hash_a), (pic_b, hash_b)
             in tqdm(combinations(hashes, 2), total=ndiffs, desc='Computing diffs')
             if abs(hash_a - hash_b) <= threshold]

    clusters = {}
    for id_a, id_b, diff in diffs:
        cluster = clusters.get(id_a, set()) | clusters.get(id_b, set()) | {id_a, id_b}
        for id in cluster:
            clusters[id] = cluster
    clusters = {frozenset(cluster) for cluster in clusters.values()}

    p = inflect.engine()
    print('Found {} {}'.format(len(clusters), p.plural('cluster', len(clusters))))
    input('Press any key to continue...')
    for cluster in clusters:
        pics = [db.pic_by_id(id) for id in cluster]
        run_gui(program=Images.factory(*pics))


if __name__ == '__main__':
    main()
