from butter.programs import Slideshow


class Main:

    def __init__(self, db=None):
        self.db = db
        self.programs = []
        self.retval = None

    @property
    def program(self):
        try:
            return self.programs[-1]
        except IndexError:
            return None

    def push(self, program):
        if self.program:
            self.program.make_uncurrent(self)
        self.programs.append(program)
        self.status_message(program.message)

    def pop(self, program, *args, **kwargs):
        assert program is self.program
        self.programs.pop()
        if self.program:
            self.program.make_current(self)
            self.status_message(self.program.message)

    def show_image(self, pic):
        raise NotImplementedError

    def status_message(self, msg):
        return self._status_message

    def _status_message(self, msg):
        raise NotImplementedError

    def popup_message(self, msg, align='center'):
        raise NotImplementedError

    def get_picker(self):
        raise NotImplementedError

    def start_timer(self, delay, callback):
        raise NotImplementedError

    def __getitem__(self, key):
        return self.db.cfg[key]
