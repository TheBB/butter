from operator import methodcaller
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox

from .utils import MainWidget, MessageDialog, PickerDialog, key_to_text
from ..main import Main
from ..programs import Slideshow



class MainWindow(Main, QMainWindow):

    def __init__(self, db=None, program=None, safe=False):
        Main.__init__(self, db=db, safe=safe)
        QMainWindow.__init__(self)
        self.setWindowTitle('Butter')
        self.setStyleSheet('background-color: black;')

        main = MainWidget()
        self.setCentralWidget(main)
        self.main = main
        self.paused = False
        self.current_pic = None

        if db:
            self.picker_dialog = PickerDialog(self.db)

        if program is None and db is not None:
            program = db.plugin_manager.get_default_program()
        (program or Slideshow)(self)

    def _show_image(self, pic):
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
        text = key_to_text(event)

        if text == 'z':
            if not self.safe:
                self.show_image(None)
            self.safe = not self.safe

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

        if text and (text.lower() in {'t'}):
            attr = {
                't': 'mark_tweak'
            }[text.lower()]
            try:
                methodcaller(attr, text.lower() == text)(self.current_pic)
            except AttributeError:
                pass
            return

        if text in {'q', 'ESC'}:
            self.close()
            return

        if self.paused:
            return

        self.program.key(self, text)


def run_gui(*args, safe=False, **kwargs):
    app = QApplication(sys.argv)
    win = MainWindow(*args, safe=safe, **kwargs)
    win.showMaximized()
    app.exec_()
    return win.retval
