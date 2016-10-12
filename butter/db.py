from os.path import join
from subprocess import run, PIPE

from sqlalchemy import create_engine, Boolean, Column, Integer, MetaData, String, Table
from sqlalchemy.orm import mapper, create_session
from sqlalchemy.sql import func
import yaml


class Database:

    def __init__(self, name, path):
        self.name = name
        self.sql_file = join(path, 'db.sqlite3')
        self.config_file = join(path, 'config.yaml')
        self.img_root = join(path, 'contents')
        self.path = path

        self.load_config()
        self.setup_db()

    def __repr__(self):
        return '<Database {}>'.format(self.name)

    def pull(self, remote=None):
        remote = remote or self.cfg['sync']['remote']
        run(['rsync', '-av', join(remote, 'config.yaml'), self.path], check=True)

    def load_config(self):
        with open(self.config_file, 'r') as f:
            cfg = yaml.load(f)

        try:
            if cfg['sync']['pull_startup'] and cfg['sync']['sync_config']:
                self.pull_config(cfg['sync']['remote'])
        except KeyError:
            pass

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
