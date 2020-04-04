#!/usr/bin/env python3
# SiliTune, a CPU power manager
# Sililib, libraries and classes for SiliTune
import sys
import os
import math
import subprocess
import logging
import time
import threading
from configparser import ConfigParser

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')


class MyCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(dpi=100)
        super(MyCanvas, self).__init__(fig)
        titles = ["CPU temp", "Power comsumption", "CPU freq"]
        self.num = 3
        self.history = 100
        self.plist = []
        self.pdatalist = []
        self._plot_ref = []
        for i in range(self.num):
            p = fig.add_subplot(311 + i)
            p.set_title(titles[i])
            self.plist.append(p)
            self.pdatalist.append(([], []))
            self._plot_ref.append(None)
            # self.plist[i].plot([1, 2], [3, 4])
            # self.plist[i].plot(self.pdatalist[i][0], self.pdatalist[i][1])

    def clear(self):
        self.pdatalist = [([], []) for _ in range(self.num)]
        for i in self.plist:
            i.cla()

    def append(self, idx, data):
        self.pdatalist[idx][0].append(time.time())
        self.pdatalist[idx][1].append(data)
        # if len(self.pdatalist[idx][0]) > self.num:
        #     self.pdatalist[idx][0] = self.pdatalist[idx][0][1:]
        #     self.pdatalist[idx][1] = self.pdatalist[idx][1][1:]
        xd = self.pdatalist[idx][0]
        yd = self.pdatalist[idx][1]
        if self._plot_ref[idx] is None:
            plot_refs = self.plist[idx].plot(xd, yd)
            self._plot_ref[idx] = plot_refs[0]
        else:
            self._plot_ref[idx].set_xdata(xd)
            self._plot_ref[idx].set_ydata(yd)
            self.plist[idx].set_xlim(min(xd), max(xd))
            self.plist[idx].set_ylim(min(yd), max(yd))
        # incremental plot needed!
        # self.plist[idx].cla()
        # self.plist[idx].plot(self.pdatalist[idx][0], self.pdatalist[idx][1])
        self.draw()
        # logging.info("Data appended")
        logging.info(self.pdatalist[idx])


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


def setcolor(obj, color):
    pal = QPalette()
    pal.setColor(QPalette.WindowText, color)
    obj.setPalette(pal)


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
        # cmdget and cmdset are functions
        self.cmdget = cmdget
        self.cmdset = cmdset

    def apply(self):
        # print(self.cmdset(self.text()))
        runcmd(self, self.cmdset(self.text()))

    def real(self):
        return runresult(None, self.cmdget)

    def reinit(self):
        self.setText(self.real())


class MyQLEMon(QLineEdit):
    def __init__(self, cmdmon, cmdplot=""):
        super().__init__()
        self.cmdmon = cmdmon
        self.cmdplot = cmdplot

    def measure(self):
        self.setText(runresult(None, self.cmdmon))

    def forplot(self):
        data = runresult(None, self.cmdplot)
        try:
            data = float(data)
            return data
        except ValueError:
            logging.error("Measured data not able to plot!")
            return 0


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


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
