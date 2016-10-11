from os.path import join


class Database:

    def __init__(self, name, path):
        self.name = name
        self.sql_file = join(path, 'db')
        self.config_file = join(path, 'config')

    def __repr__(self):
        return '<Database {}>'.format(self.name)
