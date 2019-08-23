#!/usr/bin/env python3
# SiliTune, a CPU power manager, by petergu

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sililib import *

prj_name = 'SiliTune'
prj_ver = 'v1.0'

config_file = '/etc/silitune/sili.conf'
iu_config_file = '/etc/intel-undervolt.conf'
iu_config_file_dry = './intel-undervolt.conf'

cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'

cmd_battery_check = 'cat /sys/class/power_supply/BAT0/status'

silitune_debug = 1

cpu_number = int(subprocess.getstatusoutput('ls /sys/devices/system/cpu | grep \'^cpu.$\' | wc -l')[1])

update_interval = 2
update_interval_mon = 2


checkbox_array = []
radiobtn_profile = []
underv_array = []
underv_label_array = []
underv_name = ['CPU', 'GPU', 'CPU Cache', 'System Agent', 'Analog I/O',
               'Power Short', 'Time Short', 'Power Long', 'Time Long']
undervolt_max = 150
undervolt_enabled = 0
cmd_undervolt_apply = 'intel-undervolt apply'
cmd_undervolt_read = 'intel-undervolt read'

monitor_enabled = 0

mon_checkbox = None
mon_name = ['CPU temp', 'Fan speed', 'Power consumption']
mon_cmds = ['tlp-stat -t | grep CPU | sed -e "s/^.*= *//g"',
            'sudo tlp-stat -t | grep Fan | sed -e "s/^.*= *//g"',
            'if [ `cat /sys/class/power_supply/BAT0/status` != "Discharging" ]; \
            then echo `cat /sys/class/power_supply/BAT0/status`; else \
            expr `cat /sys/class/power_supply/BAT0/voltage_now` \
            \\* `sudo tlp-stat -b | grep current_now | sed -e "s/^.*= *//g;s/ .*$//g"` \
            / 10000000 | awk \'{print $1/100 " W"}\'; fi'
            ]
mon_label_array = []
mon_array = []

profile_name = ['Power', 'Battery']
profile = -1

on_exit = 0
on_started = 0

on_front = 1

main_section_name = 'Global'

help_str = prj_name + ''' - A simple tool to tweak your CPU

You can: 
Run `tlp bat` and `tlp ac` with a click of mouse,
Disable/Enable turbo boost with a click of mouse,
Turn off/on CPU cores if you don't/do need them,
Deal with undervolting and TDP levels easily,
Monitor power consumption w/o typing commands,
Auto switch between battery and AC profiles,

See full manual on github.com/ustcpetergu/Silitune !

Just keep in mind:
Green things are quite safe to set and click;
Black things may cause system to have bad peformance or other small problems;
Red things may cause system failure, but you'll be all right after a reboot - \
set `uv enabled = 1` in ''' + config_file + ''' to enable these options!

'''


def cmd_cpu(switch, number):
    return 'echo %d > /sys/devices/system/cpu/cpu%d/online' % (switch, number)


def cmd_cpu_check(number):
    return 'cat /sys/devices/system/cpu/cpu%d/online' % number


def cmd_uv_set_uv_get(option):
    def cmd_uv_set_uv_inner(value):
        val = float(value)
        if val > 0:
            logging.warning('Undervolting value should be negative')
        elif math.fabs(val) > math.fabs(undervolt_max):
            logging.warning('Undervolting value out of range')
        else:
            return 'sed -i.bak \"s/\\(^undervolt.*\'' + underv_name[option].replace('/', '\\/') + \
                   '\'\\) *[.0-9\\-]*$/\\1 ' + value + '/g" ' + iu_config_file
        return 'false in cmd_uv_set_inner'
    return cmd_uv_set_uv_inner


def cmd_uv_set_tdp_get(option):
    def cmd_uv_set_tdp_inner(value):
        val = float(value)
        if val == 0:
            # zero means do nothing
            return 'true'
        elif val < 0:
            logging.warning('TDP and Time Window should be positive')
        else:
            if option == 5:
                return 'sed -i.bak \"s/\\(^power package\\) [0-9]*\\(.*$\\)/\\1 ' \
                       + value + '\\2/g\" ' \
                       + iu_config_file
            elif option == 6:
                return 'sed -i.bak \"s/\\(^power package [0-9]*\\/\\)[0-9]*\\(.*$\\)/\\1' \
                       + value + '\\2/g\" ' \
                       + iu_config_file
            elif option == 7:
                return 'sed -i.bak \"s/\\(^power package [0-9]*\\/[0-9]*\\) [0-9]*\\(.*$\\)/\\1 ' \
                       + value + '\\2/g\" ' \
                       + iu_config_file
            elif option == 8:
                return 'sed -i.bak \"s/\\(^power package [0-9]*\\/[0-9]* [0-9]*\\/\\)[0-9]*\\(.*$\\)/\\1' \
                       + value + '\\2/g\" ' \
                       + iu_config_file
        return 'false in cmd_uv_set_tdp_inner'
    return cmd_uv_set_tdp_inner


def cmd_uv(option, setget):
    if setget == 'set':
        if option < 5:
            return cmd_uv_set_uv_get(option)
        else:
            return cmd_uv_set_tdp_get(option)
    elif setget == 'get':
        if option < 5:
            return 'cat ' + iu_config_file + ' | grep \"^undervolt.*\"\\\'\"' + \
                   underv_name[option].replace('/', '\\/') + '\"\\\'' + \
                   ' | sed -e \"s/\'.*\'//g\" | awk \'{print $3}\''
        else:
            awkid = option - 2
            return 'cat ' + iu_config_file + ' | grep \"^power package \" | sed -e \'s/\\// /g\'' + \
                   ' | awk \'{print $%d}\'' % awkid
    else:
        return None


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
        if on_started and monitor_enabled and on_front:
            # pause measure if program is in background, to save power
            for i in mon_array:
                i.measure()
        time.sleep(update_interval_mon)


# def monitor_option():
#     pass


def init_config():
    # write the config if
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    if not config.has_section(main_section_name):
        config.add_section(main_section_name)
    global undervolt_enabled
    if config.has_option(main_section_name, 'UV Enabled'):
        undervolt_enabled = config[main_section_name]['UV Enabled'] == '1'
    else:
        print("Create config key UV Enabled")
        config[main_section_name]['UV Enabled'] = str(undervolt_enabled)
    global monitor_enabled
    if config.has_option(main_section_name, 'Enable Monitor'):
        monitor_enabled = int(config[main_section_name]['Enable Monitor'] == '1')
    else:
        print("Create config key Enable Monitor")
        config[main_section_name]['Enable Monitor'] = str(monitor_enabled)
    with open(config_file, 'w', encoding='UTF-8') as fo:
        config.write(fo)


def save_config(section):
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    config[main_section_name]['Enable Monitor'] = str(int(mon_checkbox.isChecked()))
    if not config.has_section(section):
        config.add_section(section)
    checkbox_enable_array = ['1' if i.checkbox.isChecked() else '0' for i in checkbox_array]
    config[section]['NoTurbo'] = checkbox_enable_array[0]
    for i in range(cpu_number - 1):
        config[section]['Core%d' % (i + 1)] = checkbox_enable_array[i + 1]
    for i in range(len(underv_array)):
        config[section][underv_name[i]] = underv_array[i].text()
    with open(config_file, 'w', encoding='UTF-8') as fo:
        config.write(fo)


def button_save():
    save_config(profile_name[profile])


def read_values():
    for i in checkbox_array:
        i.reinit()
    for i in underv_array:
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


def profileswitch(pid):
    global profile
    profile = pid
    section = profile_name[pid]
    config = ConfigParser()
    config.read(config_file, encoding='UTF-8')
    mon_checkbox.setChecked(int(config[main_section_name]['Enable Monitor']))
    checkbox_array[0].checkbox.setChecked(config[section]['NoTurbo'] == '1')
    checkbox_array[0].exec_change()
    for i in range(cpu_number - 1):
        checkbox_array[i + 1].checkbox.setChecked(config[section]['Core%d' % (i + 1)] == '1')
        checkbox_array[i + 1].exec_change()
    for i in range(len(underv_array)):
        try:
            underv_array[i].setText(config[section][underv_name[i]])
        except KeyError:
            logging.warning('Undervolting config not found, use 0')
            underv_array[i].setText('0')
    apply_undervolt()


def apply_undervolt():
    if undervolt_enabled:
        logging.info("Apply undervolt config...")
        for i in underv_array:
            i.apply()
        runcmd(None, cmd_undervolt_apply)
        logging.info(runresult(None, cmd_undervolt_read))
    else:
        logging.info("Undervolting not enabled.")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = prj_name
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 650
        self.logr = MyLogger()
        self.initui()

    def initui(self):
        # check if dependencies like intel-undervolt is ready
        self.check_dep()
        # Start piling up widgets
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        vbox = QVBoxLayout()
        # ----------------------------------------------
        # --------------- basic ------------------------
        # ----------------------------------------------
        # title
        hbtit = QHBoxLayout()
        ltitle = MyQLabel(prj_name + " " + prj_ver)
        hbtit.addWidget(ltitle)
        hbtit.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hbtit)
        # Help button
        bhelp = MyQButton("Help")
        bhelp.button.clicked.connect(self.showhelp)
        # print(bhelp.button.styleSheet())
        # bhelp.button.setStyleSheet('color:#00DD00')
        pal = QPalette()
        pal.setColor(QPalette.ButtonText, Qt.green)
        bhelp.setPalette(pal)
        # tlp functions
        btlpbat = MyQCmdButton("tlp bat", "tlp bat")
        btlpac = MyQCmdButton("tlp ac", "tlp ac")
        hchildbox = QHBoxLayout()
        hchildbox.addWidget(bhelp)
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
        # ----------------------------------------------
        # --------------- undervolting -----------------
        # ----------------------------------------------
        # # no undervolting enable button, enable/disable in config file
        # cb_uv = QCheckBox("Enable Undervolting", self)
        # cb_uv.clicked.connect(self.uv_enable)
        # Undervolting (including TDP control)
        for i in range(len(underv_name)):
            lab = MyQLabelRed(underv_name[i])
            underv_label_array.append(lab)
            lineedit = MyQIntLE(cmd_uv(i, 'get'), cmd_uv(i, 'set'))
            underv_array.append(lineedit)
            if not undervolt_enabled:
                lineedit.setEnabled(False)
        hbuv1 = QHBoxLayout()
        for i in [0, 1, 2]:
            hbuv1.addWidget(underv_label_array[i])
            hbuv1.addWidget(underv_array[i])
        hbuv2 = QHBoxLayout()
        for i in [3, 4]:
            hbuv2.addWidget(underv_label_array[i])
            hbuv2.addWidget(underv_array[i])
        hbuv2.setAlignment(Qt.AlignLeft)
        hbuv3 = QHBoxLayout()
        for i in [5, 6]:
            hbuv3.addWidget(underv_label_array[i])
            hbuv3.addWidget(underv_array[i])
        hbuv3.setAlignment(Qt.AlignLeft)
        hbuv4 = QHBoxLayout()
        for i in [7, 8]:
            hbuv4.addWidget(underv_label_array[i])
            hbuv4.addWidget(underv_array[i])
        hbuv4.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hbuv1)
        vbox.addLayout(hbuv2)
        vbox.addLayout(hbuv3)
        vbox.addLayout(hbuv4)
        # Undervolting apply button
        buv = QPushButton("Apply Undervolt", self)
        buv.setStyleSheet('QPushButton {color:red;}')
        buv.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buv.clicked.connect(apply_undervolt)
        if not undervolt_enabled:
            buv.setEnabled(False)
        vbox.addWidget(buv)
        # ----------------------------------------------
        # --------------- monitoring -------------------
        # ----------------------------------------------
        # Power Consumption Monitoring, CPU status monitoring
        self.ch_mon = QCheckBox("Enable Monitor", self)
        self.ch_mon.clicked.connect(self.monitor_option)
        self.ch_mon.setCheckState(False)
        pal = QPalette()
        pal.setColor(QPalette.WindowText, Qt.green)
        self.ch_mon.setPalette(pal)
        vbox.addWidget(self.ch_mon)
        global mon_checkbox
        mon_checkbox = self.ch_mon
        for i in range(len(mon_name)):
            lab = MyQLabelGreen(mon_name[i])
            mon_label_array.append(lab)
            le = MyQLEMon(mon_cmds[i])
            mon_array.append(le)
        hbmon1 = QHBoxLayout()
        for i in [0, 1]:
            hbmon1.addWidget(mon_label_array[i])
            hbmon1.addWidget(mon_array[i])
        hbmon2 = QHBoxLayout()
        for i in [2]:
            hbmon2.addWidget(mon_label_array[i])
            hbmon2.addWidget(mon_array[i])
        vbox.addLayout(hbmon1)
        vbox.addLayout(hbmon2)

        # ----------------------------------------------
        # --------------- bottom options ---------------
        # ----------------------------------------------
        # Button of Save to config file
        hboxbtm = QHBoxLayout()
        bsave = QPushButton("Save config", self)
        bsave.clicked.connect(button_save)
        bsave.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hboxbtm.addWidget(bsave)
        # Button for read real current config
        bread = QPushButton("Read Real Values", self)
        bread.clicked.connect(read_values)
        bread.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hboxbtm.addWidget(bread)
        # Open log window
        self.logr.hide()
        blog = QPushButton("Open logger", self)
        blog.clicked.connect(self.openlogger)
        blog.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hboxbtm.addWidget(blog)
        hboxbtm.setAlignment(Qt.AlignLeft)
        vbox.addLayout(hboxbtm)
        # Load config
        self.setLayout(vbox)
        self.show()
        # show that the main app has started
        global on_started
        on_started = 1

    def openlogger(self):
        self.logr.show()

    def check_dep(self):
        if runcmd(self, 'ls ' + iu_config_file) != 0:
            QMessageBox.warning(self, '',
                                'intel-undervolt configure file not found, undervolt functions will not work',
                                QMessageBox.Yes)

    def showhelp(self):
        QMessageBox.information(self, prj_name + ' Help',
                                help_str,
                                QMessageBox.Yes)

    def monitor_option(self):
        global monitor_enabled
        monitor_enabled = int(self.ch_mon.isChecked())


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None, body=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)
        menu.triggered.connect(self.actions)
        menu.addAction("To Power")
        menu.addAction("To Battery")
        menu.addAction("Show")
        menu.addAction("Hide")
        menu.addAction("Exit")
        self.setContextMenu(menu)
        self.body = body

    def actions(self, q):
        text = q.text()
        print(text + " is triggered from system tray.")
        global on_front
        if text == 'Exit':
            QCoreApplication.exit()
        elif text == 'Show':
            self.body.show()
            on_front = 1
        elif text == 'Hide':
            self.body.hide()
            on_front = 0
        elif text == 'To Power':
            profileswitch_pgm(0)
        elif text == 'To Battery':
            profileswitch_pgm(1)


if __name__ == '__main__':
    print(prj_name + " started running...")
    if os.getuid() != 0:
        print("Are you r00t?")
        exit(-1)
    app = QApplication(sys.argv)
    thr1 = threading.Thread(target=thrautoswitch, name="AutoSwitchThread")
    thr1.start()
    thr2 = threading.Thread(target=thrmonitor, name="MonitoringThread")
    thr2.start()
    init_config()
    ex = App()
    w = QWidget()
    trayIcon = SystemTrayIcon(QIcon("icon.png"), w, body=ex)
    trayIcon.show()
    app.exec_()
    # It's a kinda ugly thread here
    on_exit = 1
    thr1.join()
    thr2.join()
    print("Goodbye.")
    sys.exit(0)
