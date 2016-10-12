import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout, QMainWindow,
    QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget
)

class ImageView(QLabel):

    def __init__(self):
        super(ImageView, self).__init__()
        self.setMinimumSize(1,1)
        self.setAlignment(Qt.Alignment(0x84))
        self.setStyleSheet('QLabel { background-color: black; }')

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


# class ButtonsWidget(QWidget):

#     def __init__(self, target):
#         super(ButtonsWidget, self).__init__()

#         cancel_btn = QPushButton('Cancel')
#         cancel_btn.clicked.connect(target.reject)
#         cancel_btn.setDefault(False)
#         cancel_btn.setAutoDefault(False)

#         ok_btn = QPushButton('OK')
#         ok_btn.setDefault(True)
#         ok_btn.clicked.connect(target.accept)

#         self.setLayout(QHBoxLayout())
#         self.layout().addWidget(cancel_btn)
#         self.layout().addWidget(ok_btn)



# class PickerWidget(QWidget):

#     def __init__(self, picker):
#         super(PickerWidget, self).__init__()

#         self.picker = picker

#         layout = QHBoxLayout()
#         self.setLayout(layout)

#         checkbox = QCheckBox(picker.name)
#         checkbox.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
#         checkbox.setMinimumWidth(100)
#         checkbox.stateChanged.connect(self.check)
#         layout.addWidget(checkbox)
#         self.checkbox = checkbox

#         slider = QSlider(Qt.Horizontal)
#         slider.setMinimumWidth(300)
#         slider.setMinimum(0)
#         slider.setMaximum(100)
#         slider.setValue(100)
#         slider.valueChanged.connect(self.slide)
#         layout.addWidget(slider)
#         self.slider = slider

#         label = QLabel('0%')
#         label.setMinimumWidth(40)
#         label.setAlignment(Qt.AlignRight)
#         layout.addWidget(label)
#         self.label = label

#         layout.setSizeConstraint(QLayout.SetFixedSize)

#     def check(self, state):
#         self.slider.setVisible(state == Qt.Checked)
#         self.label.setVisible(state == Qt.Checked)
#         if state == Qt.Checked:
#             self.slide(self.slider.value())
#         else:
#             self.slide(0)

#     def slide(self, value):
#         self.label.setText('{}%'.format(value))

#     @property
#     def checked(self):
#         return self.checkbox.checkState() == Qt.Checked

#     @property
#     def frequency(self):
#         return self.slider.value()


class MessageDialog(QDialog):

    def __init__(self, text, callback=None):
        super(MessageDialog, self).__init__()
        self.setWindowTitle('PTools')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel()
        label.setStyleSheet('''QLabel {
            background-color: rgba(0, 0, 0, 200);
            color: rgb(255, 255, 255);
        }''')
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


# class PickerDialog(QDialog):

#     def __init__(self, db):
#         super(PickerDialog, self).__init__()
#         self.setWindowTitle('Pickers')
#         self.db = db
#         self.widgets = [PickerWidget(p) for p in db.pickers]

#         layout = QVBoxLayout()
#         self.setLayout(layout)

#         for w in self.widgets:
#             layout.addWidget(w)

#         layout.addWidget(ButtonsWidget(self))

#         self.setFixedSize(self.sizeHint())
#         for w in self.widgets:
#             w.check(False)

#     def get_picker(self):
#         union = UnionPicker()
#         for w in self.widgets:
#             if w.checked and w.frequency:
#                 union.add(w.picker, w.frequency)
#         if not union.pickers:
#             return self.db.picker()
#         return union


# class FlagsDialog(QDialog):

#     def __init__(self, db):
#         super(FlagsDialog, self).__init__()
#         self.setWindowTitle('Flags')

#         layout = QVBoxLayout()
#         self.setLayout(layout)

#         grid = QGridLayout()
#         layout.addLayout(grid)

#         self.assignment, self.defaults = {}, {}
#         for i, c in enumerate(db.custom_columns, start=1):
#             if isinstance(c.type, Boolean):
#                 widget = QCheckBox(c.title)
#                 self.defaults[widget] = Qt.Checked if c.default.arg else Qt.Unchecked
#                 grid.addWidget(widget, i, 1, 1, 2)
#             elif isinstance(c.type, Integer):
#                 label = QLabel(c.title)
#                 widget = QSpinBox()
#                 self.defaults[widget] = c.default.arg
#                 grid.addWidget(label, i, 1)
#                 grid.addWidget(widget, i, 2)
#             self.assignment[c.key] = widget

#         layout.addWidget(ButtonsWidget(self))

#         self.set_defaults()

#     def exec_(self):
#         self.set_defaults()
#         return super(FlagsDialog, self).exec_()

#     def set_defaults(self):
#         for w, v in self.defaults.items():
#             if isinstance(w, QCheckBox):
#                 w.setCheckState(Qt.Checked if v else Qt.Unchecked)
#             elif isinstance(w, QSpinBox):
#                 w.setValue(v)

#     def get_flags(self):
#         ret = {}
#         for k, w in self.assignment.items():
#             if isinstance(w, QCheckBox):
#                 ret[k] = w.checkState() == Qt.Checked
#             elif isinstance(w, QSpinBox):
#                 ret[k] = w.value()

#         return ret
