import sys
from string import ascii_lowercase

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox

from .utils import ImageView, MessageDialog #, FlagsDialog, PickerDialog
from ..programs import Slideshow


KEY_MAP = {
    Qt.Key_Space: 'SPC',
    Qt.Key_Escape: 'ESC',
    Qt.Key_Tab: 'TAB',
    Qt.Key_Return: 'RET',
    Qt.Key_Backspace: 'BSP',
    Qt.Key_Delete: 'DEL',
    Qt.Key_Up: 'UP',
    Qt.Key_Down: 'DOWN',
    Qt.Key_Left: 'LEFT',
    Qt.Key_Right: 'RIGHT',
}
KEY_MAP.update({
    getattr(Qt, 'Key_{}'.format(s.upper())): s
    for s in ascii_lowercase
})


class MainWindow(QMainWindow):

    def __init__(self, db=None, program=Slideshow):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Butter')
        self.db = db

        image = ImageView()
        self.setCentralWidget(image)
        self.image = image
        self.paused = False
        self.current_pic = None

        # self.picker_dialog = PickerDialog(self.db)
        # self.flags_dialog = FlagsDialog(self.db)

        self.programs = []

        if program:
            program(self)

    def register(self, program):
        self.programs.append(program)

    def unregister(self, *args, **kwargs):
        self.programs.pop()
        # self.programs[-1].make_current(self, *args, **kwargs)

    @property
    def program(self):
        return self.programs[-1]

    def show_image(self, pic):
        self.current_pic = pic
        self.image.load(pic)

    def show_message(self, msg, align='center'):
        if isinstance(msg, str):
            msg = [msg]
        text = ''.join('<p align="{}">{}</p>'.format(align, m) for m in msg)
        retval = []
        MessageDialog(text, lambda e: retval.append(e))
        return retval[0]

    # def start_timer(self, delay, callback):
    #     timer = QTimer(self)
    #     timer.timeout.connect(lambda: callback(self, timer))
    #     timer.start(delay)
    #     return timer

    def keyPressEvent(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier

        try:
            text = KEY_MAP[event.key()]
        except KeyError:
            return

        if shift and text.isupper():
            text = 'S-{}'.format(text)
        elif shift:
            text = text.upper()
        if ctrl:
            text = 'C-{}'.format(text)

        if text == 'p':
            if self.paused:
                self.image.load(self.current_pic)
                self.program.unpause(self)
            else:
                self.image.load(None)
                self.program.pause(self)
            self.paused = not self.paused
            return

        if text in {'q', 'ESC'}:
            self.close()
            return

        if self.paused:
            return

        self.program.key(self, text)


def run_gui(*args, **kwargs):
    app = QApplication(sys.argv)
    win = MainWindow(*args, **kwargs)
    win.showMaximized()
    return app.exec_()
