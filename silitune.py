#!/usr/bin/env python3
# SiliTune, a CPU power manager, by petergu

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sililib import *

config_file = '/etc/silitune/sili.conf'
iu_config_file = '/etc/intel-undervolt.conf'

cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'

cmd_battery_check = 'cat /sys/class/power_supply/BAT0/status'

silitune_debug = 1

cpu_number = int(subprocess.getstatusoutput('ls /sys/devices/system/cpu | grep \'^cpu.$\' | wc -l')[1])

update_interval = 1
update_interval_mon = 1


checkbox_array = []
radiobtn_profile = []

profile_name = ['Power', 'Battery']
profile = -1

on_exit = 0
on_started = 0


def cmd_cpu(switch, number):
    return 'echo %d > /sys/devices/system/cpu/cpu%d/online' % (switch, number)


def cmd_cpu_check(number):
    return 'cat /sys/devices/system/cpu/cpu%d/online' % number


def dummy():
    print("Dummy")


def on_power():
    sts, out = subprocess.getstatusoutput(cmd_battery_check)
    if out == 'Charging' or out == "Full":
        return True
    else:
        return False


# thread for auto switch between AC and battery
def thrautoswitch():
    on_power_now = -1
    while not on_exit:
        if on_started:
            on_power_last = on_power_now
            on_power_now = on_power()
            if on_power_last != on_power_now:
                if on_power_now:
                    logging.debug("Switch to AC")
                    profileswitch_pgm(0)
                else:
                    logging.debug("Switch to battery")
                    profileswitch_pgm(1)
        time.sleep(update_interval)


# thread for system monitoring and monitored value updating
def thrmonitor():
    while not on_exit:
        if on_started:
            pass
        time.sleep(update_interval_mon)


def save_config(section):
    try:
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
    except PermissionError:
        logging.error('No permission to write configure file %s!' % config_file)


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


# Programmatically switch profile: manually set button
def profileswitch_pgm(pid):
    radiobtn_profile[pid].setChecked(True)
    profileswitch(pid)


# TODO: bug here, multi thread call this before initialize cause list index out of range
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


def apply_undervolt():
    logging.info("Apply undervolt config...")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "SiliTune"
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 640
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
        hchildbox.setAlignment(Qt.AlignLeft)
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
        hb1.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hb1)
        # CPU Turbo
        hb2 = QHBoxLayout()
        cboxturbo = MyQCheckBox("Disable Turbo", cmd_turbo_no, cmd_turbo_yes, cmd_turbo_get)
        cboxturbo.reinit()
        checkbox_array.append(cboxturbo)
        hb2.addWidget(cboxturbo)
        hb2.setAlignment(Qt.AlignLeft)
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
        hb_core.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hb_core)
        # Power Consumption Monitoring, CPU status monitoring
        # Undervolting
        lcpu = MyQLabelRed('CPU')
        lgpu = MyQLabelRed('GPU')
        lcache = MyQLabelRed('CPU Cache')
        lsa = MyQLabelRed('System Agent')
        laio = MyQLabelRed('Analog I/O')
        ecpu = MyQIntLE()
        egpu = MyQIntLE()
        ecache = MyQIntLE()
        esa = MyQIntLE()
        eaio = MyQIntLE()
        hbuv1 = QHBoxLayout()
        hbuv1.addWidget(lcpu)
        hbuv1.addWidget(ecpu)
        hbuv1.addWidget(lgpu)
        hbuv1.addWidget(egpu)
        hbuv1.addWidget(lcache)
        hbuv1.addWidget(ecache)
        hbuv1.setAlignment(Qt.AlignLeft)
        hbuv2 = QHBoxLayout()
        hbuv2.addWidget(lsa)
        hbuv2.addWidget(esa)
        hbuv2.addWidget(laio)
        hbuv2.addWidget(eaio)
        hbuv2.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hbuv1)
        vbox.addLayout(hbuv2)
        # TDP Control
        lpowershort = MyQLabelRed('Power Short')
        lpowershorttime = MyQLabelRed('Time Short')
        lpowerlong = MyQLabelRed('Power Long')
        lpowerlongtime = MyQLabelRed('Time Long')
        epowershort = MyQIntLE()
        epowershorttime = MyQIntLE()
        epowerlong = MyQIntLE()
        epowerlongtime = MyQIntLE()
        hbuv3 = QHBoxLayout()
        hbuv4 = QHBoxLayout()
        hbuv3.addWidget(lpowershort)
        hbuv3.addWidget(epowershort)
        hbuv3.addWidget(lpowershorttime)
        hbuv3.addWidget(epowershorttime)
        hbuv3.setAlignment(Qt.AlignLeft)
        hbuv4.addWidget(lpowerlong)
        hbuv4.addWidget(epowerlong)
        hbuv4.addWidget(lpowerlongtime)
        hbuv4.addWidget(epowerlongtime)
        hbuv4.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hbuv3)
        vbox.addLayout(hbuv4)
        # Undervolting apply button
        buv = QPushButton("Apply Undervolt", self)
        buv.setStyleSheet('QPushButton {color:red;}')
        buv.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buv.clicked.connect(apply_undervolt)
        vbox.addWidget(buv)
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
        # show that the main app has started
        global on_started
        on_started = 1

    def openlogger(self):
        self.logr.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    thr1 = threading.Thread(target=thrautoswitch, name="AutoSwitchThread")
    thr1.start()
    thr2 = threading.Thread(target=thrmonitor, name="MonitoringThread")
    thr2.start()
    # what if thread begin to update values before main app run and GUI start?
    # maybe no effect maybe causing crash
    ex = App()
    w = QWidget()
    trayIcon = SystemTrayIcon(QIcon("icon.png"), w, body=ex)
    trayIcon.show()
    app.exec_()
    # It's a kinda ugly thread here
    on_exit = 1
    thr1.join()
    thr2.join()
    sys.exit(0)
