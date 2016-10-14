import sys
from string import ascii_lowercase

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox

from .utils import MainWidget, MessageDialog, PickerDialog
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
    Qt.Key_Minus: '-',
    Qt.Key_Plus: '+',
    Qt.Key_Equal: '=',
}
KEY_MAP.update({
    getattr(Qt, 'Key_{}'.format(s.upper())): s
    for s in ascii_lowercase
})


class MainWindow(QMainWindow):

    default_program = Slideshow

    def __init__(self, db=None, program=None):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Butter')
        self.setStyleSheet('background-color: black;')
        self.db = db

        main = MainWidget()
        self.setCentralWidget(main)
        self.main = main
        self.paused = False
        self.current_pic = None

        if db:
            self.picker_dialog = PickerDialog(self.db)

        self.programs = []

        program = program or self.default_program
        program(self)

    def register(self, program):
        self.programs.append(program)
        self.status_message(program.message)

    def unregister(self, *args, **kwargs):
        self.programs.pop()
        self.program.make_current(self)
        self.status_message(self.program.message)

    @property
    def program(self):
        return self.programs[-1]

    def show_image(self, pic):
        self.current_pic = pic
        self.main.load(pic)

    def status_message(self, value=None):
        if value is None:
            value = self.program.message
        self.main.message(value)

    def popup_message(self, msg, align='center'):
        if isinstance(msg, str):
            msg = [msg]
        text = ''.join('<p align="{}">{}</p>'.format(align, m) for m in msg)
        retval = []
        MessageDialog(text, lambda e: retval.append(e))
        return retval[0]

    def get_picker(self):
        if self.picker_dialog.exec_() == QDialog.Accepted:
            return self.picker_dialog.picker
        return None

    def start_timer(self, delay, callback):
        timer = QTimer(self)
        timer.timeout.connect(lambda: callback(self))
        timer.start(delay)
        return timer

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
                self.main.load(self.current_pic)
                self.program.unpause(self)
                self.status_message()
            else:
                self.main.load(None)
                self.program.pause(self)
                self.status_message('')
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
