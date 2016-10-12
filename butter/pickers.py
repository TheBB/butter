from sqlalchemy.sql import func


class FilterPicker:

    def __init__(self, db, *filters):
        self.filters = filters
        self.db = db
        # self.name = name

    def get(self):
        return self.db.query().filter(*self.filters).order_by(func.random()).first()

    def get_all(self):
        return self.db.query()


class RandomPicker(FilterPicker):

    def __init__(self, db):
        super(RandomPicker, self).__init__(db)
