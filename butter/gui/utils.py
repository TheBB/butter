import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout, QMainWindow,
    QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget
)

from ..pickers import UnionPicker


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

        self.image = ImageView()
        self.label = QLabel()
        self.label.setMaximumHeight(25)
        self.label.setStyleSheet('color: rgb(200, 200, 200);')

        font = QFont()
        font.setPixelSize(20)
        font.setWeight(QFont.Bold)
        self.label.setFont(font)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.image)
        self.layout().addWidget(self.label)

    def load(self, *args, **kwargs):
        self.image.load(*args, **kwargs)

    def message(self, msg):
        self.label.setText('<div align="center">{}</div>'.format(msg))


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
        if self.callback:
            self.callback(event.text())
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
