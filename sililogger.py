#!/usr/bin/env python3
# SiliTune, a CPU power manager
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


# A simple logger, use this, so pop-up windows can be canceled
# https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MyLogger(QDialog, QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.setWindowTitle("SiliTune logger")
        self.setGeometry(800, 0, 800, 400)

        # logging.basicConfig(level=logging.DEBUG,
        #                     format='%(asctime)s %(levelname)s - %(message)s',
        #                     datefmt='%H:%M:%S'
        #                     )
        logTextBox = QTextEditLogger(self)
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:\n %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)

        self._button = QPushButton(self)
        self._button.setText('Test Me')

        layout = QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        layout.addWidget(self._button)
        self.setLayout(layout)

        # Connect signal to slot
        self._button.clicked.connect(self.test)

    def test(self):
        logging.debug('damn, a bug')
        logging.info('something to remember')
        logging.warning('that\'s not right')
        logging.error('foobar')


def openlogger():
    dlg = MyLogger()
    dlg.show()
    dlg.raise_()


# class MyLogger(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.title = "SiliTune Logger"
#         self.left = 0
#         self.top = 0
#         self.width = 640
#         self.height = 480
#         self.initui()
#
#     def initui(self):
#         self.show()

