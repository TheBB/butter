from collections import namedtuple
from random import choice


BoundFunction = namedtuple('BoundFunction', ['key', 'fn'])

def bind(key=None):
    return lambda fn: BoundFunction(key, fn)


class ProgramMeta(type):

    def __new__(cls, name, bases, attrs):
        keymap = {}
        for b in bases:
            if hasattr(b, 'keymap'):
                keymap.update(b.keymap)
        for k, v in attrs.items():
            if isinstance(v, BoundFunction):
                keymap[v.key] = v.fn
                attrs[k] = v.fn
        if 'keymap' in attrs:
            keymap.update(attrs['keymap'])
        attrs['keymap'] = keymap
        return type.__new__(cls, name, bases, attrs)


class Program(metaclass=ProgramMeta):

    def key(self, m, key):
        if key in self.keymap:
            self.keymap[key](self, m)
        if None in self.keymap:
            self.keymap[None](self, m)

    def pause(self, m):
        pass

    def unpause(self, m):
        pass


class Slideshow(Program):

    def __init__(self, m, picker=None):
        m.register(self)
        self.picker = picker or m.db.default_picker()
        self.pic(m)

    @bind()
    def pic(self, m):
        m.show_image(self.picker.get())


class SingleImage(Program):

    def __init__(self, m, img):
        m.register(self)
        m.show_image(img)

    @classmethod
    def factory(cls, img):
        return lambda m: cls(m, img)
