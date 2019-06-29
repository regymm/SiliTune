#!/usr/bin/env python3
# SiliTune, a CPU power manager
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'cat 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'cat 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'


def runcmd(cmd, msg='Command returned a non-zero value, maybe something wrong happened'):
    sts, out = subprocess.getstatusoutput(cmd)
    print(out)
    if sts != 0:
        print('%s' % msg)
    return sts


class myQCmdButton(QWidget):
    def __init__(self, name='default', cmd='pwd'):
        super().__init__()
        # self.setMinimumSize(1, 50)
        self.name = name
        self.cmd = cmd
        self.button = QPushButton(self.name, self)
        # self.button.move(100, 100)
        self.button.clicked.connect(self.exec)
        self.button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def exec(self):
        stat = runcmd(self.cmd)
        if stat != 0:
            QMessageBox.question(self, 'Info', 'Non-zero return value returned. Error may have occured.', QMessageBox.Ok)


class myQLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(myQLabel, self).__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignLeading)
        # self.setSizePolicy(QSizePolicy.Ig, QSizePolicy.Fixed)



class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "SiliTune"
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 480
        self.initui()

    def initui(self):
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        ltitle = myQLabel("SiliTune v1.0")
        btlpbat = myQCmdButton("tlp bat", "tlp bat")
        btlpac = myQCmdButton("tlp ac", "tlp ac")
        vbox = QVBoxLayout()
        hchildbox = QHBoxLayout()
        vbox.addWidget(ltitle)
        hchildbox.addWidget(btlpbat)
        hchildbox.addWidget(btlpac)
        vbox.addLayout(hchildbox)
        self.setLayout(vbox)
        # grid = QGridLayout()
        # # grid.setSpacing(0)
        # grid.addWidget(ltitle, 0, 0)
        # grid.addWidget(btlpbat, 1, 0)
        # grid.addWidget(btlpac, 1, 1)
        # btn = myQCmdButton(name='turbo', cmd='uname -a')
        # grid.addWidget(btn, 2, 0)
        # # grid.addWidget(label2, 2, 0)
        # # grid.addWidget(label3, 3, 0)
        #
        # self.setLayout(grid)
        self.show()

    # @pyqtSlot()
    # def on_click(self):
    #     stas = runcmd(cmd_turbo_get)
    #     # if stas != 0:
    #     QMessageBox.question(self, 'Info', 'Non-zero return value caught. Error may have occured.', QMessageBox.Ok)
    #     print('Disable turbo ...')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

