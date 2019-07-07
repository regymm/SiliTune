#!/usr/bin/env python3
# SiliTune, a CPU power manager
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'

silitune_debug = 1

# cpu_number = int(subprocess.getstatusoutput('grep -c ^processor /proc/cpuinfo')[1])
cpu_number = 8


def cmd_cpu(switch, number):
    return 'echo %d > /sys/devices/system/cpu/cpu%d/online' % (switch, number)


def cmd_cpu_check(number):
    return 'cat /sys/devices/system/cpu/cpu%d/online' % number


msg_error = 'Command returned a non-zero value, maybe something wrong happened'


def runcmd(obj, cmd, msg=msg_error):
    if silitune_debug:
        print("Running command: \n" + cmd)
    sts, out = subprocess.getstatusoutput(cmd)
    print(out)
    if sts != 0:
        print('%s' % msg)
        QMessageBox.question(obj, 'Error', msg + '\nCommand:' + cmd + '\nMessage:' + out, QMessageBox.Ok)
    return sts


def runcheck(obj, cmd, msg=msg_error):
    sts, out = subprocess.getstatusoutput(cmd)
    if sts != 0:
        print('%s' % msg)
        QMessageBox.question(obj, 'Error', msg + '\nCommand:' + cmd + '\nMessage:' + out, QMessageBox.Ok)
    return int(out)


class MyQCmdButton(QWidget):
    def __init__(self, name='default', cmd='pwd'):
        super().__init__()
        # self.setMinimumSize(1, 50)
        self.name = name
        self.cmd = cmd
        self.button = QPushButton(self.name, self)
        # self.button.move(100, 100)
        self.button.clicked.connect(self.exec)
        self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.setMinimumSize(200, 200)

    def exec(self):
        runcmd(self, self.cmd)


class MyQLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(MyQLabel, self).__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignLeading)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class MyQCheckBox(QCheckBox):
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
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.checkbox.setMinimumHeight(200)
        # self.checkbox.setMinimumSize(320, 320)

    def exec_change(self):
        if self.checkbox.isChecked():
            print('on')
            runcmd(self, self.cmdon)
        else:
            runcmd(self, self.cmdoff)

    def reinit(self):
        if runcheck(self, self.cmdget):
            # self.checkbox.setCheckState(Qt.Checked)
            self.checkbox.setChecked(Qt.Checked)
        else:
            self.checkbox.setCheckState(Qt.Unchecked)



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
        vbox = QVBoxLayout()
        # title
        ltitle = MyQLabel("SiliTune v1.0")
        vbox.addWidget(ltitle)
        # tlp functions
        btlpbat = MyQCmdButton("tlp bat", "tlp bat")
        btlpac = MyQCmdButton("tlp ac", "tlp ac")
        hchildbox = QHBoxLayout()
        hchildbox.addWidget(btlpbat)
        hchildbox.addWidget(btlpac)
        vbox.addLayout(hchildbox)
        # CPU Turbo
        hb2 = QHBoxLayout()
        cboxturbo = MyQCheckBox("Disable Turbo", cmd_turbo_no, cmd_turbo_yes, cmd_turbo_get)
        cboxturbo.reinit()
        hb2.addWidget(cboxturbo)
        vbox.addLayout(hb2)
        # CPU Cores
        hb_core = QHBoxLayout()
        core_array = []
        for i in range(cpu_number):
            core = MyQCheckBox("%d" % i, cmd_cpu(1, i), cmd_cpu(0, i), cmd_cpu_check(i))
            if i == 0:
                core.checkbox.setCheckState(Qt.Checked)
                core.checkbox.setDisabled(True)
            else:
                core.reinit()
            core_array.append(core)
            hb_core.addWidget(core)
        vbox.addLayout(hb_core)
        # Power Consumption Monitoring
        self.setLayout(vbox)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
