#!/usr/bin/env python3
# SiliTune, a CPU power manager
# Sililib, libraries and classes for SiliTune
import sys
import os
import math
import subprocess
import logging
# from elevate import elevate
import time
import threading
from configparser import ConfigParser

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

msg_error = 'None-zero returned, command may have failed'


def runcmd(obj, cmd, msg=msg_error):
    sts, out = subprocess.getstatusoutput(cmd)
    if sts != 0:
        # logging.info(out)
        logging.error('Error:' + msg + '\nCommand:' + cmd + '\nMessage:' + out)
    return sts


def runresult(obj, cmd, msg=msg_error):
    sts, out = subprocess.getstatusoutput(cmd)
    if sts != 0:
        logging.error('Error:' + msg + '\nCommand:' + cmd + '\nMessage:' + out)
    return out


def runcheckTF(obj, cmd, msg=msg_error):
    if runresult(obj, cmd, msg) == '1':
        return True
    else:
        return False


class MyQCmdButton(QWidget):
    def __init__(self, name='default', cmd='true'):
        super().__init__()
        # self.setMinimumSize(1, 50)
        self.name = name
        self.cmd = cmd
        self.button = QPushButton(self.name, self)
        # self.button.move(100, 100)
        self.button.clicked.connect(self.exec)
        # self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.setMinimumSize(200, 200)

    def exec(self):
        runcmd(self, self.cmd)

    def sizeHint(self):
        return self.button.sizeHint()


class MyQButton(QWidget):
    def __init__(self, name):
        super().__init__()
        self.button = QPushButton(name, self)

    def sizeHint(self):
        return self.button.sizeHint()


class MyQLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(MyQLabel, self).__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignLeading)
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class MyQLabelRed(MyQLabel):
    def __init__(self, *args, **kwargs):
        super(MyQLabelRed, self).__init__(*args, **kwargs)
        pal = QPalette()
        pal.setColor(QPalette.WindowText, Qt.red)
        self.setPalette(pal)


class MyQLabelGreen(MyQLabel):
    def __init__(self, *args, **kwargs):
        super(MyQLabelGreen, self).__init__(*args, **kwargs)
        pal = QPalette()
        pal.setColor(QPalette.WindowText, Qt.green)
        self.setPalette(pal)


class MyQIntLE(QLineEdit):
    def __init__(self, cmdget, cmdset):
        super().__init__()
        self.setValidator(QIntValidator())
        self.setMaxLength(5)
        # self.setAlignment(Qt.AlignRight)
        # self.setFixedWidth(50)
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # mysterous size code copied from stackovfl
        fm = self.fontMetrics()
        m = self.textMargins()
        c = self.contentsMargins()
        w = 4*fm.width('x')+m.left()+m.right()+c.left()+c.right()
        self.setFixedWidth(2 * w)
        self.cmdget = cmdget
        self.cmdset = cmdset

    def apply(self):
        # print(self.cmdset(self.text()))
        runcmd(self, self.cmdset(self.text()))

    def real(self):
        return runresult(self, self.cmdget)

    def reinit(self):
        self.setText(self.real())


class MyQCheckBox(QWidget):
    # when the checkbox is toggled "on" or "off", command cmdon or cmdoff will be run.
    # when the program initialized or profile switched, a run of command cmdget will return 0 or 1,
    # indicating the current status of the checkbox should be "on" or "off"
    def __init__(self, name, cmdon="uname", cmdoff="uname", cmdget="uname"):
        super().__init__()
        self.name = name
        self.cmdon = cmdon
        self.cmdoff = cmdoff
        self.cmdget = cmdget
        self.checkbox = QCheckBox(self.name, self)
        self.checkbox.clicked.connect(self.exec_change)
        # self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # self.checkbox.setMinimumHeight(200)
        # self.checkbox.setMinimumSize(320, 320)

    def exec_change(self):
        if self.checkbox.isChecked():
            runcmd(self, self.cmdon)
        else:
            runcmd(self, self.cmdoff)

    def real(self):
        return runcheckTF(self, self.cmdget)

    def reinit(self):
        self.checkbox.setChecked(self.real())

    def sizeHint(self):
        return self.checkbox.sizeHint()


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None, body=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)
        menu.triggered.connect(self.exitt)
        menu.addAction("Exit")
        menu.addAction("Show")
        menu.addAction("Hide")
        menu.addAction("To Power")
        menu.addAction("To Battery")
        self.setContextMenu(menu)
        self.body = body

    def exitt(self, q):
        text = q.text()
        print(text + " is triggered from system tray.")
        if text == 'Exit':
            QCoreApplication.exit()
        elif text == 'Show':
            self.body.show()
        elif text == 'Hide':
            self.body.hide()
        elif text == 'To Power':
            profileswitch_pgm(0)
        elif text == 'To Battery':
            profileswitch_pgm(1)


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

        # self._button = QPushButton(self)
        # self._button.setText('Clear')

        layout = QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        # layout.addWidget(self._button)
        self.setLayout(layout)

        # # Connect signal to slot
        # self._button.clicked.connect(self.clearlog)

    # def clearlog(self):
    #     self.logTextBox.set

    # def test(self):
    #     logging.debug('damn, a bug')
    #     logging.info('something to remember')
    #     logging.warning('that\'s not right')
    #     logging.error('foobar')


# # A simple logger, use this, so pop-up windows can be canceled
# # https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
# class QTextEditLogger(logging.Handler):
#     def __init__(self, parent):
#         super().__init__()
#         self.widget = QPlainTextEdit(parent)
#         self.widget.setReadOnly(True)
#
#     def emit(self, record):
#         msg = self.format(record)
#         self.widget.appendPlainText(msg)
#
#
# class MyLogger(QDialog, QPlainTextEdit):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#         font = QFont()
#         font.setPointSize(10)
#         self.setFont(font)
#         self.setWindowTitle("SiliTune logger")
#         self.setGeometry(800, 0, 800, 400)
#
#         # logging.basicConfig(level=logging.DEBUG,
#         #                     format='%(asctime)s %(levelname)s - %(message)s',
#         #                     datefmt='%H:%M:%S'
#         #                     )
#         logTextBox = QTextEditLogger(self)
#         # You can format what is printed to text box
#         logTextBox.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:\n %(message)s'))
#         logging.getLogger().addHandler(logTextBox)
#         # You can control the logging level
#         logging.getLogger().setLevel(logging.DEBUG)
#
#         self._button = QPushButton(self)
#         self._button.setText('Test Me')
#
#         layout = QVBoxLayout()
#         # Add the new logging box widget to the layout
#         layout.addWidget(logTextBox.widget)
#         layout.addWidget(self._button)
#         self.setLayout(layout)
#
#         # Connect signal to slot
#         self._button.clicked.connect(self.test)
#
#     def test(self):
#         logging.debug('damn, a bug')
#         logging.info('something to remember')
#         logging.warning('that\'s not right')
#         logging.error('foobar')
#
#
# def openlogger():
#     dlg = MyLogger()
#     dlg.show()
#     dlg.raise_()


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

