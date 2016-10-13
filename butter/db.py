from collections import namedtuple, OrderedDict
from os import listdir
from os.path import basename, exists, join, splitext
from subprocess import run, PIPE
import re
import readline
import sys

import inflect
from sqlalchemy import create_engine, Boolean, Column, Integer, MetaData, String, Table
from sqlalchemy.orm import mapper, create_session
from sqlalchemy.sql import func
import yaml

from .pickers import FilterPicker, RandomPicker, UnionPicker
from .programs import SingleImage
from .gui import run_gui


def set_paths(obj, path):
    obj.sql_file = join(path, 'db.sqlite3')
    obj.config_file = join(path, 'config.yaml')
    obj.img_root = join(path, 'contents')
    obj.staging_root = join(path, 'staging')
    obj.path = path


def rsync(source, destination, say=False):
    ret = run(['rsync', '-a', '--info=stats2', '--delete', source, destination],
              check=True, stdout=PIPE)
    stdout = ret.stdout.decode()
    nnew = int(re.search(r'Number of created files: (?P<n>\d+)', stdout).group('n'))
    ndel = int(re.search(r'Number of deleted files: (?P<n>\d+)', stdout).group('n'))
    if say or nnew > 0:
        print('{} new'.format(nnew))
    if say or ndel > 0:
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

    def sync(self, push=True, pull=True, stage=True, verbose=False):
        if (push or pull) and ('sync' not in self.cfg or 'remote' not in self.cfg['sync']):
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
            for c in deleted_on_hd:
                delete_ids.add(int(splitext(basename(c))[0][:-1]))

        deleted_in_db = existing_hd - existing_db
        if deleted_in_db or verbose:
            n = len(deleted_in_db)
            print('{} {} deleted from database, re-staging'.format(n, p.plural('image', n)))
            for fn in deleted_in_db:
                run(['mv', fn, join(self.staging_root, basename(fn))], stdout=PIPE, check=True)

        if pull or push:
            remote_contents = join(self.cfg['sync']['remote'], 'contents', '')
            local_contents = join(self.img_root, '')

        if pull:
            print('Fetching data from remote...')
            nnew, ndel = rsync(remote_contents, local_contents, say=verbose)

        db = self.database()

        if delete_ids:
            for pic in db.query().filter(db.Picture.id.in_(delete_ids)):
                db.delete(pic)
            db.session.commit()

        if stage:
            for fn in listdir(self.staging_root):
                self.flag(join(self.staging_root, fn), db)

        if push:
            print('Sending data to remote...')
            nnew, ndel = rsync(local_contents, remote_contents, say=verbose)

    def flag(self, fn, db):
        print('Staged: {}'.format(fn))
        run_gui(program=SingleImage.factory(fn))
        extension = splitext(fn)[-1].lower()
        if extension == '.jpeg':
            extension = '.jpg'

        pic = db.Picture()
        pic.extension = extension[1:]
        while True:
            s = input('>>> ')
            if s == 'view':
                run_gui(program=SingleImage.factory(fn))
            elif s in {'skip', 'done'}:
                if s == 'skip':
                    pic = None
                break
            elif s == '?':
                print(pic)
            else:
                try:
                    if '=' in s:
                        key, value = s.split('=')
                        pic.assign_field(key, eval(value))
                    else:
                        value = True
                        if s.startswith('not'):
                            value = False
                            s = s[3:]
                        pic.assign_field(s, value)
                except AttributeError as e:
                    print(e)

        if pic:
            db.session.add(pic)
            db.session.commit()
            run(['mv', fn, pic.filename], stdout=PIPE, check=True)
            print('Committed as {}'.format(basename(pic.filename)))

    def database(self):
        return Database(self.name, self.path)


class Field(Column):

    FieldType = namedtuple('FieldType', ['pytype', 'sqltype', 'default'])

    __types = {
        'bool': FieldType(bool, Boolean, False),
        'int': FieldType(int, Integer, 0),
    }

    def __init__(self, key, type, aliases=[]):
        self.typestr = type
        super(Field, self).__init__(key, type_=self.sql_type, nullable=False, default=self.default_value)
        self.__aliases = {a.lower() for a in aliases}
        self.__aliases.add(key.lower())

    @property
    def py_type(self):
        return self.__types[self.typestr].pytype

    @property
    def sql_type(self):
        return self.__types[self.typestr].sqltype

    @property
    def default_value(self):
        return self.__types[self.typestr].default

    def matches(self, key):
        return key.lower() in self.__aliases


class Database:

    def __init__(self, name, path):
        self.name = name
        set_paths(self, path)

        self.load_config()
        self.setup_db()
        self.make_pickers()

    def __repr__(self):
        return '<Database {}>'.format(self.name)

    def load_config(self):
        with open(self.config_file, 'r') as f:
            cfg = yaml.load(f)
        self.cfg = cfg

    def setup_db(self):
        class Picture:
            root = self.img_root
            fields = []

            @property
            def filename(self):
                return join(self.root, '{idx:0>8}.{ext}'.format(idx=self.id, ext=self.extension))

            def __repr__(self):
                return '<Pic {}>'.format(self.filename)

            def assign_field(self, key, value):
                key = key.strip().lower()
                for field in self.fields:
                    if field.matches(key):
                        setattr(self, field.key, value)
                        return
                raise AttributeError("No such field: '{}'".format(key))

            def __str__(self):
                return '\n'.join('{} = {}'.format(field.key, getattr(self, field.key))
                                 for field in self.fields)

        columns = [
            Column('id', Integer, primary_key=True),
            Column('extension', String, nullable=False),
            Column('delt', Boolean, nullable=False, default=False),
        ]
        for c in self.cfg['fields']:
            field = Field(**c)
            columns.append(field)
            Picture.fields.append(field)

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

    def delete_ids(self):
        return {p.id for p in self.query().filter(self.Picture.delt == True)}

    def delete(self, pic):
        if exists(pic.filename):
            run(['rm', pic.filename], check=True)
        self.session.delete(pic)

    def picker(self, filters=[]):
        if not filters:
            if hasattr(self, 'default_picker'):
                return self.default_picker
            return RandomPicker(self)

        if isinstance(filters[0], list):
            picker = UnionPicker(self)
            for f in filters:
                freq = 1.0
                if f and isinstance(f[0], float):
                    freq, f = f[0], f[1:]
                picker.add(self.picker(f), freq)
            return picker

        filters = [eval(s, None, self.Picture.__dict__) for s in filters]
        return FilterPicker(self, *filters)

    def make_pickers(self):
        self.pickers = OrderedDict()
        if not 'pickers' in self.cfg:
            return
        for spec in self.cfg['pickers']:
            name, filters = next(iter(spec.items()))
            self.pickers[name] = self.picker(filters)
