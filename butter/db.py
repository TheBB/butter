from os import listdir
from os.path import basename, join, splitext
from subprocess import run, PIPE
import re
import sys

import inflect
from sqlalchemy import create_engine, Boolean, Column, Integer, MetaData, String, Table
from sqlalchemy.orm import mapper, create_session
from sqlalchemy.sql import func
import yaml

from .pickers import RandomPicker
from .programs import single_image
from .gui import run_gui


def set_paths(obj, path):
    obj.sql_file = join(path, 'db.sqlite3')
    obj.config_file = join(path, 'config.yaml')
    obj.img_root = join(path, 'contents')
    obj.staging_root = join(path, 'staging')
    obj.path = path


def rsync(source, destination, say=None):
    ret = run(['rsync', '-a', '--info=stats2', '--delete', source, destination],
              check=True, stdout=PIPE)
    stdout = ret.stdout.decode()
    nnew = int(re.search(r'Number of created files: (?P<n>\d+)', stdout).group('n'))
    ndel = int(re.search(r'Number of deleted files: (?P<n>\d+)', stdout).group('n'))
    if say or say is None and nnew > 0:
        print('{} new'.format(nnew))
    if say or say is None and ndel > 0:
        print('{} deleted'.format(ndel))
    return nnew, ndel


class DatabaseLoader:

    def __init__(self, name, path):
        self.name = name
        set_paths(self, path)

        self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            cfg = yaml.load(f)
        self.cfg = cfg

    def sync(self, verbose=None):
        if 'sync' not in self.cfg or 'remote' not in self.cfg['sync']:
            raise Exception('No remote configured')

        print('Synchronizing {}...'.format(self.name))

        db = self.database()
        p = inflect.engine()

        delete_ids = db.delete_ids()
        if delete_ids or verbose:
            n = len(delete_ids)
            print('{} {} scheduled for deletion'.format(n, p.plural('image', n)))

        existing_hd = {join(db.img_root, fn) for fn in listdir(db.img_root)}
        existing_db = {pic.filename for pic in db.query()}

        deleted_on_hd = existing_db - existing_hd
        if deleted_on_hd or verbose:
            n = len(deleted_on_hd)
            print('{} {} deleted from disk, deleting also from database'.format(n, p.plural('image', n)))
            delete_ids.update(deleted_on_hd)

        deleted_in_db = existing_hd - existing_db
        if deleted_in_db or verbose:
            n = len(deleted_in_db)
            print('{} {} deleted from database, re-staging'.format(n, p.plural('image', n)))
            for fn in deleted_in_db:
                run(['mv', fn, join(self.staging_root, basename(fn))], stdout=PIPE, check=True)

        remote_contents = join(self.cfg['sync']['remote'], 'contents') + '/'
        local_contents = self.img_root + '/'

        print('Fetching data from remote...')
        nnew, ndel = rsync(remote_contents, local_contents, say=verbose)

        # TODO: Delete images in `delete_ids`

        # TODO: Staging
        for fn in listdir(self.staging_root):
            print('Staged: {}'.format(fn))
            run_gui(program=single_image(join(self.staging_root, fn)))

        print('Sending data to remote...')
        nnew, ndel = rsync(local_contents, remote_contents, say=verbose)

    def database(self):
        return Database(self.name, self.path)


class Database:

    def __init__(self, name, path):
        self.name = name
        set_paths(self, path)

        self.load_config()
        self.setup_db()

    def __repr__(self):
        return '<Database {}>'.format(self.name)

    def load_config(self):
        with open(self.config_file, 'r') as f:
            cfg = yaml.load(f)
        self.cfg = cfg

    def setup_db(self):
        class Picture:
            root = self.img_root

            @property
            def filename(self):
                return join(self.root, '{idx:0>8}.{ext}'.format(idx=self.id, ext=self.extension))

            def __repr__(self):
                return '<Pic {}>'.format(self.filename)

        columns = [
            Column('id', Integer, primary_key=True),
            Column('extension', String, nullable=False),
            Column('delt', Boolean, nullable=False, default=False),
        ]
        for c in self.cfg['fields']:
            if isinstance(c, str):
                kind = Integer if c.startswith('num_') else Boolean
                name = c.replace('_', ' ').title()
                key = c
            else:
                kind = {'int': Integer, 'bool': Boolean}[c['type']]
                name = c['title']
                key = c['key']
            default = {Integer: 0, Boolean: False}[kind]
            col = Column(key, type_=kind, nullable=False, default=default)
            col.title = name
            columns.append(col)

        self.engine = create_engine('sqlite:///{}'.format(self.sql_file))
        metadata = MetaData(bind=self.engine)
        table = Table('pictures', metadata, *columns)
        metadata.create_all()
        mapper(Picture, table)

        self.Picture = Picture
        self.update_session()

    def update_session(self):
        if hasattr(self, 'session'):
            self.session.close()
        self.session = create_session(bind=self.engine, autocommit=False, autoflush=True)

    def query(self):
        return self.session.query(self.Picture)

    def default_picker(self):
        return RandomPicker(self)

    def delete_ids(self):
        return {p.id for p in self.query().filter(self.Picture.delt == True)}
