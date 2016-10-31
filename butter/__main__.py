import click
import imagehash
import inflect
from itertools import combinations
import multiprocessing
from os.path import basename, join, splitext
from PIL import Image
import requests
import shutil
from tempfile import TemporaryDirectory
from tqdm import tqdm
from . import cfg
from .gui import run_gui
from .programs import Images, Upgrade as UpgradeProgram
from .upgrade import Upgrade


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


@main.command('show-upgrades')
@cfg.db_argument()
def show_upgrades(db):
    pics = list(db.upgrade_pics())
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


def download_url(url, path, base):
    try:
        _, ext = splitext(url)
    except:
        ext = '.jpg'
    try:
        response = requests.get(url, stream=True)
        target = join(path, base + ext)
        with open(target, 'wb') as out:
            shutil.copyfileobj(response.raw, out)
        return target
    except:
        pass

def upgrade_pic(pic, u, number):
    alternatives = [pic]
    urls = []
    cmds = ['view', 'search', 'get', 'choose']
    p = inflect.engine()
    print(basename(pic.filename))
    with TemporaryDirectory() as path:
        while True:
            s = input('>>> ').strip()
            if not s:
                s, cmds = cmds[0], cmds[1:]
            if s == 'view':
                run_gui(program=Images.factory(pic))
            elif s == 'skip':
                return
            elif s == 'search':
                urls = u.potential_urls(pic.filename, number)
                print('Found {} {}'.format(len(urls), p.plural('URL', len(urls))))
                for url in urls:
                    print(url)
            elif s == 'get':
                alternatives = [pic]
                for i, url in enumerate(urls):
                    target = download_url(url, path, str(i))
                    if target:
                        alternatives.append(target)
                print('Have {} {}'.format(
                    len(alternatives), p.plural('alternative', len(alternatives)))
                )
            elif s == 'choose':
                run_gui(program=UpgradeProgram.factory(pic, *alternatives))
                pic.upg = False
                pic.db.session.commit()
                return

@main.command()
@click.option('--number', '-n', type=int, default=5)
@cfg.db_argument()
def upgrade(db, number):
    sync(pull=True, push=False, stage=False)
    pics = list(db.upgrade_pics())
    p = inflect.engine()
    if not pics:
        return
    with Upgrade() as u:
        while pics:
            pic, pics = pics[0], pics[1:]
            upgrade_pic(pic, u, number)
    sync(push=True, pull=False, stage=False)


if __name__ == '__main__':
    main()
