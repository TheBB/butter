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
from .programs import Images, Upgrade as UpgradeProgram, PickOne
from .upgrade import Upgrade


@click.group(invoke_without_command=True)
@click.option('--no-plugins', 'allow_plugins', default=True, flag_value=False)
@click.option('--plugin', '-p', 'plugins', multiple=True, type=str)
@click.pass_context
def main(ctx, plugins, allow_plugins):
    """Extensible image database tool."""
    ctx.obj = cfg
    cfg.load_plugins = allow_plugins
    for plugin in plugins:
        cfg.load_plugin(plugin)
    if ctx.invoked_subcommand is None:
        ctx.invoke(gui)


@main.command('list')
def list_dbs():
    """Show a list of databases."""
    for db in cfg.databases():
        print(db)


@main.command()
@cfg.db_argument()
def status(db):
    """Show basic information about a database."""
    with db.database(regular=False) as db:
        print(db)


@main.command()
@cfg.db_argument()
def gui(db):
    """Launch the GUI."""
    with db.database(regular=True) as db:
        run_gui(db=db)


@main.command()
@click.option('--push/--no-push', default=True)
@click.option('--pull/--no-pull', default=True)
@click.option('--stage/--no-stage', default=True)
@click.option('-v', '--verbose', default=False, is_flag=True)
@cfg.db_argument()
def sync(db, **kwargs):
    """Synchronize a database."""
    db.sync(**kwargs)


@main.command('push-config')
@cfg.db_argument()
def push_config(db):
    """Push config to remote."""
    db.push_config()


@main.command('show-tweaks')
@cfg.db_argument()
def show_tweaks(db):
    with db.database(regular=False) as db:
        pics = list(db.tweak_pics())
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
    with db.database(regular=False) as db:
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
            run_gui(program=PickOne.factory(*pics))


def download_url(url, path, base):
    try:
        _, ext = splitext(url)
        ext = ext.split('?')[0]
    except:
        ext = '.jpg'
    try:
        response = requests.get(url, stream=True, timeout=10)
        target = join(path, base + ext)
        with open(target, 'wb') as out:
            shutil.copyfileobj(response.raw, out)
        return target
    except:
        pass

def upgrade_pic(pic, u, number, prompt='>>> '):
    alternatives = [pic]
    urls = []
    cmds = ['view', 'search', 'get', 'choose']
    p = inflect.engine()
    with TemporaryDirectory() as path:
        urls = u.potential_urls(pic.filename, number)
        print('Found {} {}'.format(len(urls), p.plural('URL', len(urls))))
        alternatives = [pic]
        for i, url in enumerate(urls):
            target = download_url(url, path, str(i))
            if target:
                alternatives.append(target)
        print('Have {} {}'.format(
            len(alternatives), p.plural('alternative', len(alternatives)))
        )
        run_gui(program=UpgradeProgram.factory(pic, *alternatives))
        pic.db.session.commit()

@main.command()
@click.option('--samples', '-s', type=int, default=5)
@cfg.db_argument()
def tweak(db, samples):
    with db.database(regular=False) as db, Upgrade() as u, TemporaryDirectory() as path:
        pics = list(db.tweak_pics())
        for i, pic in enumerate(pics):
            run_gui(program=Images.factory(pic))
            while True:
                prompt = '({}/{}) >>> '.format(i+1, len(pics))
                s = input(prompt).strip()
                if s in {'', 'skip'}:
                    break
                elif s == 'done':
                    return
                elif s == 'view':
                    run_gui(program=Images.factory(pic))
                elif s in {'a', 'app', 'approve'}:
                    pic.mark_tweak(False)
                    break
                elif s in {'u', 'up', 'upgrade'}:
                    upgrade_pic(pic, u, samples, prompt=prompt)
                    pic.mark_tweak(False)
                    break
                elif s in {'d', 'del', 'delete'}:
                    db.delete(pic)
                    break


if __name__ == '__main__':
    main()
