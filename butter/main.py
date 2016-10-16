from .programs import Slideshow


class Main:

    default_program = Slideshow

    def __init__(self, db=None, cfg=None):
        if cfg:
            self.cfg = cfg
        else:
            try:
                self.cfg = db.cfg
            except AttributeError:
                self.cfg = {}
        self.db = db
        self.programs = []

    @property
    def program(self):
        try:
            return self.programs[-1]
        except IndexError:
            return None

    def register(self, program):
        if self.program:
            self.program.make_uncurrent(self)
        self.programs.append(program)
        self.status_message(program.message)

    def unregister(self, program, *args, **kwargs):
        assert program is self.program
        self.programs.pop()
        if self.program:
            self.program.make_current(self)
            self.status_message(self.program.message)

    def show_image(self, pic):
        pass

    def status_message(self, msg):
        pass

    def popup_message(self, msg, align='center'):
        return None

    def get_picker(self):
        return None

    def start_timer(self, delay, callback):
        return None

    def __getitem__(self, key):
        return self.cfg[key]
