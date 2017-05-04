from collections import namedtuple
from os.path import basename
from random import choice


BoundFunction = namedtuple('BoundFunction', ['keys', 'fn'])

def bind(*keys):
    keys = keys or None
    return lambda fn: BoundFunction(keys, fn)


class ProgramMeta(type):

    def __new__(cls, name, bases, attrs):
        keymap = {}
        for b in bases:
            if hasattr(b, 'keymap'):
                keymap.update(b.keymap)
        for k, v in attrs.items():
            if isinstance(v, BoundFunction):
                if v.keys is None:
                    keymap[None] = v.fn
                else:
                    for key in v.keys:
                        keymap[key] = v.fn
                attrs[k] = v.fn
        if 'keymap' in attrs:
            keymap.update(attrs['keymap'])
        attrs['keymap'] = keymap
        return type.__new__(cls, name, bases, attrs)


class Program(metaclass=ProgramMeta):

    __message = ''

    def __init__(self, m):
        self.m = m
        m.register(self)

    def key(self, m, key):
        if key in self.keymap:
            self.keymap[key](self, m)
            return
        if None in self.keymap:
            self.keymap[None](self, m)

    @property
    def message(self):
        return self.__message

    @message.setter
    def message(self, value):
        self.__message = value
        self.m.status_message(value)

    def pause(self, m):
        pass

    def unpause(self, m):
        pass

    def make_current(self, m):
        pass

    def make_uncurrent(self, m):
        pass

    @classmethod
    def factory(cls, *args, **kwargs):
        return lambda m: cls(m, *args, **kwargs)

    @classmethod
    def bind(cls, key, callback, *args, **kwargs):
        cls.keymap[key] = lambda obj, m: callback(obj, m, *args, **kwargs)


class FromPicker(Program):

    def __init__(self, m, picker=None):
        super(FromPicker, self).__init__(m)
        self.picker = picker or m.db.picker()

    @bind()
    def pic(self, m, set_msg=True, pic=None):
        pic = pic or self.picker.get()
        m.show_image(pic)
        if set_msg:
            self.message = '{}'.format(pic.id)
        return pic


class Slideshow(FromPicker):

    def __init__(self, m, picker=None):
        super(Slideshow, self).__init__(m, picker)
        self.timer = None
        self.delay = 1000.0
        self.pic(m)

    def make_uncurrrent(self):
        if self.timer:
            self.timer.stop()

    def make_currrent(self):
        if self.timer:
            self.timer.start()

    @bind('P')
    def select_picker(self, m):
        picker = m.get_picker()
        if picker:
            self.picker = picker
        self.pic(m)

    @bind('t')
    def automate(self, m):
        if self.timer:
            self.timer.stop()
            self.timer = None
        else:
            self.timer = m.start_timer(self.delay, self.pic)

    @bind('+', '=')
    def inc_delay(self, m):
        self.delay += 250
        if self.timer:
            self.timer.setInterval(self.delay)

    @bind('-')
    def dec_delay(self, m):
        self.delay = max(250.0, self.delay - 250)
        if self.timer:
            self.timer.setInterval(self.delay)


class Images(Program):

    _index = 0

    def __init__(self, m, *images):
        super(Images, self).__init__(m)
        self.images = list(images)
        self.index = 0
        self.show_image(m)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value % len(self.images)

    def show_image(self, m):
        img = self.images[self.index]
        m.show_image(img)

        try:
            fn = img.filename
        except AttributeError:
            fn = img
        self.message = '({}/{}) {}'.format(self.index+1, len(self.images), basename(fn))

    @bind('j', 'n', 'SPC', 'RIGHT', 'DOWN')
    def next(self, m):
        self.index += 1
        self.show_image(m)

    @bind('k', 'p', 'BSP', 'LEFT', 'UP')
    def prev(self, m):
        self.index -= 1
        self.show_image(m)

    @bind()
    def quit(self, m):
        m.close()


class Upgrade(Images):

    def __init__(self, m, target, *images):
        super(Upgrade, self).__init__(m, *images)
        self.target = target

    @bind('RET')
    def pick(self, m):
        img = self.images[self.index]
        if isinstance(img, str):
            self.target.replace_with(img)
        self.quit(m)

    @bind('d')
    def drop(self, m):
        del self.images[self.index]
        self.index = self.index
        self.show_image(m)


class PickOne(Images):

    def __init__(self, m, *images):
        super(PickOne, self).__init__(m, *images)

    @bind('RET')
    def pick(self, m):
        for i, pic in enumerate(self.images):
            if i != self.index:
                pic.db.delete(pic)
        self.quit(m)

    @bind('d')
    def drop(self, m):
        pic = self.images[self.index]
        pic.db.delete(pic)
        del self.images[self.index]
        self.index = self.index
        self.show_image(m)
