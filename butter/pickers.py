from itertools import repeat
from random import uniform

from sqlalchemy.sql import func


class FilterPicker:

    def __init__(self, db, *filters):
        self.filters = filters
        self.db = db

    def get(self):
        return self.db.query().filter(*self.filters).order_by(func.random()).first()

    def get_all(self):
        return self.db.query().filter(*self.filters)

    def get_dist(self):
        pics = list(self.get_all())
        prob = 1 / len(pics)
        yield from zip(pics, repeat(prob))


class RandomPicker(FilterPicker):

    def __init__(self, db):
        super(RandomPicker, self).__init__(db)


class TraversePicker:

    def __init__(self, picker):
        self.pics = iter(picker.get_all())

    def get(self):
        try:
            return next(self.pics)
        except:
            return None


class UnionPicker:

    def __init__(self, db):
        self.pickers = []
        self.db = db

    def add(self, picker, frequency=1.0):
        self.pickers.append((picker, float(frequency)))

    def get(self):
        max = sum(f for _, f in self.pickers)
        r = uniform(0.0, max)

        for p, f in self.pickers:
            r -= f
            if r <= 0.0:
                break

        return p.get()

    def get_all(self, probs=False):
        for p, f in self.pickers:
            if f > 0.0:
                yield from p.get_all(probs)

    def get_dist(self):
        for p, f in self.pickers:
            if f > 0.0:
                for pic, prob in p.get_dist():
                    yield (pic, prob * f)
