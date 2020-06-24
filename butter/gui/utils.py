from string import ascii_lowercase
import sys
from os import path

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout, QMainWindow,
    QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget,
    QGraphicsBlurEffect,
)

from ..pickers import UnionPicker


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

def key_to_text(event):
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

    return text


class ImageView(QLabel):

    def __init__(self):
        super(ImageView, self).__init__()
        self.setMinimumSize(1,1)
        self.setAlignment(Qt.Alignment(0x84))

        self.orig_pixmap = None

    def load(self, pic):
        if not pic:
            self.orig_pixmap = QPixmap()
        else:
            if isinstance(pic, str):
                fn = pic
            else:
                fn = pic.filename
            self.orig_pixmap = QPixmap(fn)
        self.resize()

    def resize(self):
        if not self.orig_pixmap:
            return
        if not self.orig_pixmap.isNull():
            pixmap = self.orig_pixmap.scaled(self.width(), self.height(), 1, 1)
        else:
            pixmap = self.orig_pixmap
        self.setPixmap(pixmap)

    def resizeEvent(self, event):
        self.resize()


class MainWidget(QWidget):

    def __init__(self):
        super(MainWidget, self).__init__()

        self._blur = QGraphicsBlurEffect()
        self._blur.setBlurRadius(0)

        self.image = ImageView()
        self.image.setGraphicsEffect(self._blur)

        self.video = QVideoWidget()

        self.label = QLabel()
        self.label.setMaximumHeight(25)
        self.label.setStyleSheet('color: rgb(200, 200, 200);')

        font = QFont()
        font.setPixelSize(20)
        font.setWeight(QFont.Bold)
        self.label.setFont(font)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.image)
        self.layout().addWidget(self.video)
        self.layout().addWidget(self.label)

        self.mplayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mplayer.setVideoOutput(self.video)

        self.mplayer.error.connect(lambda: print("Video:", self.mplayer.errorString()))
        self.mplayer.mediaStatusChanged.connect(self.state_changed)

        self.overlay = QLabel(self)
        self.overlay.setFrameStyle(Qt.FramelessWindowHint)
        self.overlay.setStyleSheet('background-color: rgba(0,0,0,0.7); color: rgba(200,200,200,1);')
        self.overlay.setFont(font)
        self.overlay.setVisible(False)
        self.overlay.setWordWrap(True)

    def resize(self):
        self.overlay.setGeometry(0, 3*self.height()//4 - 50, self.width(), 100)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize()

    def state_changed(self, state):
        if state == QMediaPlayer.EndOfMedia:
            self.mplayer.setPosition(0)
            self.mplayer.play()

    @property
    def blur(self):
        return self._blur.blurRadius()

    @blur.setter
    def blur(self, value):
        self._blur.setBlurRadius(value)

    def load(self, pic, *args, **kwargs):
        if isinstance(pic, str):
            still = path.splitext(pic)[1].lower()[1:] not in ('webm', 'mp4')
        else:
            still = pic.is_still if pic else True

        if still:
            self.image.load(pic, *args, **kwargs)
            self.video.hide()
            self.image.show()
            self.mplayer.stop()
        else:
            url = pic if isinstance(pic, str) else pic.filename
            self.mplayer.setMedia(QMediaContent(QUrl.fromLocalFile(url)))
            self.mplayer.setMuted(True)
            self.mplayer.play()
            self.image.hide()
            self.video.show()

        self.overlay.setVisible(False)

    def message(self, msg):
        self.label.setText('<div align="center">{}</div>'.format(msg))

    def flash(self, msg):
        self.overlay.setText('<div align="center">{}</div>'.format(msg))
        self.overlay.setVisible(True)

    def halt(self):
        self.mplayer.stop()


class ButtonsWidget(QWidget):

    def __init__(self, target):
        super(ButtonsWidget, self).__init__()

        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(target.reject)
        cancel_btn.setDefault(False)
        cancel_btn.setAutoDefault(False)

        ok_btn = QPushButton('OK')
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(target.accept)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(cancel_btn)
        self.layout().addWidget(ok_btn)


class PickerWidget(QWidget):

    def __init__(self, name, picker):
        super(PickerWidget, self).__init__()

        self.picker = picker

        layout = QHBoxLayout()
        self.setLayout(layout)

        checkbox = QCheckBox(name)
        checkbox.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        checkbox.setMinimumWidth(100)
        checkbox.stateChanged.connect(self.check)
        layout.addWidget(checkbox)
        self.checkbox = checkbox

        slider = QSlider(Qt.Horizontal)
        slider.setMinimumWidth(300)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(100)
        slider.valueChanged.connect(self.slide)
        layout.addWidget(slider)
        self.slider = slider

        label = QLabel('0%')
        label.setMinimumWidth(40)
        label.setAlignment(Qt.AlignRight)
        layout.addWidget(label)
        self.label = label

        layout.setSizeConstraint(QLayout.SetFixedSize)

    def check(self, state):
        self.slider.setVisible(state == Qt.Checked)
        self.label.setVisible(state == Qt.Checked)
        if state == Qt.Checked:
            self.slide(self.slider.value())
        else:
            self.slide(0)

    def slide(self, value):
        self.label.setText('{}%'.format(value))

    @property
    def checked(self):
        return self.checkbox.checkState() == Qt.Checked

    @property
    def frequency(self):
        return self.slider.value()


class MessageDialog(QDialog):

    def __init__(self, text, callback=None):
        super(MessageDialog, self).__init__()
        self.setWindowTitle('Butter')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel()
        label.setStyleSheet("""QLabel {
            background-color: rgba(0, 0, 0, 200);
            color: rgb(255, 255, 255);
        }""")
        label.setText(text)
        label.setMargin(20)

        font = QFont()
        font.setPixelSize(32)
        font.setWeight(QFont.Bold)
        label.setFont(font)

        layout.addWidget(label)

        self.callback = callback
        self.exec_()

    def keyPressEvent(self, event):
        key = key_to_text(event)
        if not key:
            return
        if self.callback:
            self.callback(key)
        self.accept()


class PickerDialog(QDialog):

    def __init__(self, db):
        super(PickerDialog, self).__init__()
        self.setWindowTitle('Pickers')
        self.db = db
        self.widgets = [PickerWidget(name, p) for name, p in db.pickers.items()]

        layout = QVBoxLayout()
        self.setLayout(layout)

        for w in self.widgets:
            layout.addWidget(w)

        layout.addWidget(ButtonsWidget(self))

        self.setFixedSize(self.sizeHint())
        for w in self.widgets:
            w.check(False)

    @property
    def picker(self):
        union = UnionPicker(self.db)
        for w in self.widgets:
            if w.checked and w.frequency:
                union.add(w.picker, w.frequency)
        if not union.pickers:
            return self.db.picker()
        return union
