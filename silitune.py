#!/usr/bin/env python3
# SiliTune, a CPU power manager
import sys
import os
import subprocess
import logging
import time
import threading
from configparser import ConfigParser

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import sililogger


config_file = './sili.conf'

cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'

cmd_battery_check = 'cat /sys/class/power_supply/BAT0/status'

silitune_debug = 1

# cpu_number = int(subprocess.getstatusoutput('grep -c ^processor /proc/cpuinfo')[1])
cpu_number = 8

update_interval = 1

checkbox_array = []
radiobtn_profile = []

profile_name = ['Power', 'Battery']
profile = -1

on_exit = 0

# def openlogger(obj):
#     print(obj)
#     # logr = sililogger.MyLogger()
#     obj.logr = MyLogger()
#     # print(logr)
#     obj.logr.show()


def cmd_cpu(switch, number):
    return 'echo %d > /sys/devices/system/cpu/cpu%d/online' % (switch, number)


def cmd_cpu_check(number):
    return 'cat /sys/devices/system/cpu/cpu%d/online' % number


def dummy():
    print("Dummy")


msg_error = 'None-zero returned, command may have failed'


def runcmd(obj, cmd, msg=msg_error):
    # if silitune_debug:
    #     logging.debug("Running command: \n" + cmd)
    sts, out = subprocess.getstatusoutput(cmd)
    # logging.info(out)
    if sts != 0:
        logging.error('Error:' + msg + '\nCommand:' + cmd + '\nMessage:' + out)
    return sts


def runcheck(obj, cmd, msg=msg_error):
    sts, out = subprocess.getstatusoutput(cmd)
    if sts != 0:
        # logging.info(out)
        logging.error('Error: ' + msg + '\nCommand:' + cmd + '\nMessage:' + out)
    if out == '1':
        return True
    else:
        return False


def on_power():
    sts, out = subprocess.getstatusoutput(cmd_battery_check)
    if out == 'Charging' or out == "Full":
        return True
    else:
        return False


def thrautoswitch():
    while not on_exit:
        if on_power():
            logging.debug("On AC")
        else:
            logging.debug("On battery")
        time.sleep(update_interval)


def save_config(section):
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    if not config.has_section(section):
        config.add_section(section)
    checkbox_enable_array = ['1' if i.checkbox.isChecked() else '0' for i in checkbox_array]
    config[section]['NoTurbo'] = checkbox_enable_array[0]
    for i in range(cpu_number - 1):
        config[section]['Core%d' % (i + 1)] = checkbox_enable_array[i + 1]
    with open(config_file, 'w', encoding='UTF-8') as fo:
        config.write(fo)


def button_save():
    save_config(profile_name[profile])


def read_values():
    for i in checkbox_array:
        i.reinit()


def profileswitch_btn(self):
    for i in range(len(radiobtn_profile)):
        if radiobtn_profile[i].isChecked():
            logging.debug("Switch to profile %s" % profile_name[i])
            profileswitch(i)
    # if self.bgprofile.checkedID() == 10:
    #     print("Switch to Power profile")
    # elif self.bgprofile.checkedID() == 11:
    #     print("Switch to Battery profile")
    # else:
    #     print("Unknown profile!")


def profileswitch(pid):
    global profile
    profile = pid
    section = profile_name[pid]
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    checkbox_array[0].checkbox.setChecked(config[section]['NoTurbo'] == '1')
    checkbox_array[0].exec_change()
    for i in range(cpu_number - 1):
        checkbox_array[i + 1].checkbox.setChecked(config[section]['Core%d' % (i + 1)] == '1')
        checkbox_array[i + 1].exec_change()


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
        return runcheck(self, self.cmdget)

    def reinit(self):
        self.checkbox.setChecked(self.real())


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "SiliTune"
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 480
        self.logr = MyLogger()
        self.initui()

    def initui(self):
        font = QFont()
        font.setPointSize(14)
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
        # Radiobutton for profile switch
        lprofile = MyQLabel("Profile")
        # bgprofile = QButtonGroup()
        rbpower = QRadioButton("Power", self)
        rbbatt = QRadioButton("Battery", self)
        rbpower.clicked.connect(profileswitch_btn)
        rbbatt.clicked.connect(profileswitch_btn)
        radiobtn_profile.append(rbpower)
        radiobtn_profile.append(rbbatt)
        # rbpower.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # rbbatt.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hb1 = QHBoxLayout()
        hb1.addWidget(lprofile)
        # hb1.addWidget(bgprofile)
        hb1.addWidget(rbpower)
        hb1.addWidget(rbbatt)
        vbox.addLayout(hb1)
        # CPU Turbo
        hb2 = QHBoxLayout()
        cboxturbo = MyQCheckBox("Disable Turbo", cmd_turbo_no, cmd_turbo_yes, cmd_turbo_get)
        cboxturbo.reinit()
        checkbox_array.append(cboxturbo)
        hb2.addWidget(cboxturbo)
        vbox.addLayout(hb2)
        # CPU Cores
        core_label = MyQLabel("CPU Cores")
        vbox.addWidget(core_label)
        hb_core = QHBoxLayout()
        for i in range(cpu_number):
            core = MyQCheckBox("%d" % i, cmd_cpu(1, i), cmd_cpu(0, i), cmd_cpu_check(i))
            if i == 0:
                # the cpu0 cannot be offlined, it's a dummy
                core.checkbox.setCheckState(Qt.Checked)
                core.checkbox.setDisabled(True)
            else:
                core.reinit()
                checkbox_array.append(core)
            hb_core.addWidget(core)
        vbox.addLayout(hb_core)
        # Power Consumption Monitoring
        # Undervolting
        # TDP Control
        # Button of Save to config file
        bsave = QPushButton("Save config", self)
        bsave.clicked.connect(button_save)
        bsave.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        vbox.addWidget(bsave)
        # Button for read real current config
        bread = QPushButton("Read Real Values", self)
        bread.clicked.connect(read_values)
        bread.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        vbox.addWidget(bread)
        # Open log window
        self.logr.hide()
        blog = QPushButton("Open logger", self)
        blog.clicked.connect(self.openlogger)
        blog.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        vbox.addWidget(blog)
        # Load config

        self.setLayout(vbox)
        self.show()

    def openlogger(self):
        self.logr.show()


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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    thr1 = threading.Thread(target=thrautoswitch, name="AutoSwitchThread")
    thr1.start()
    ex = App()
    app.exec_()
    on_exit = 1
    thr1.join()
    sys.exit(0)
