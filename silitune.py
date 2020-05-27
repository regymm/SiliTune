#!/usr/bin/env python3
# SiliTune, a CPU power manager, by petergu

import sys
sys.path.append("/usr/lib/silitune")
from sililib import *

prj_name = 'SiliTune'
prj_ver = 'v1.1'
prj_license = 'GPLv3'
prj_website = 'github.com/ustcpetergu/SiliTune'

config_file = '/etc/silitune.conf'
data_dir = '/var/lib/silitune'
image_dir = '/usr/lib/silitune'
iu_config_file = '/etc/intel-undervolt.conf'

cmd_turbo_get = 'cat /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_no = 'echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo'
cmd_turbo_yes = 'echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo'


# detect battery name
def detect_battery(name):
    try:
        os.stat("/sys/class/power_supply/{}/status".format(name))
        return True
    except FileNotFoundError:
        return False


batt_names_possible = ['BAT0', 'BAT1']
batt_name = None

for name in batt_names_possible:
    if detect_battery(name):
        batt_name = name

if batt_name == None:
    logging.error('battery name invalid!')
    batt_name = "---"

cmd_battery_check = 'cat /sys/class/power_supply/{}/status'.format(batt_name)

silitune_debug = 1

cpu_number = int(subprocess.getstatusoutput('ls /sys/devices/system/cpu | grep \'^cpu.$\' | wc -l')[1])

update_interval_switch = 2
update_interval_mon = 2

checkbox_array = []
radiobtn_profile = []
uvsetbtn = None
underv_array = []
underv_label_array = []
underv_name = ['CPU', 'GPU', 'CPU Cache', 'System Agent', 'Analog I/O',
               'Power Short', 'Time Short', 'Power Long', 'Time Long']
undervolt_max = 450
undervolt_enabled = 0
cmd_undervolt_apply = 'intel-undervolt apply'
cmd_undervolt_read = 'intel-undervolt read'

cmd_sync_disk = 'sync; sleep 0.1'

cmd_bench_small = '7z b -md22 -mmt4'
# cmd_bench_small = '7z b -mmt4'

monitor_enabled = 0

mon_checkbox = None
mon_name = ['CPU temp', 'Fan speed', 'Battery', 'CPU freq']
batt_volt = runresult(None, 'cat /sys/class/power_supply/{}/voltage_now'.format(batt_name))
mon_label_array = []
mon_array = []

profile_name = ['Power', 'Battery']
profile = -1

on_front = 1

main_section_name = 'Global'

help_str = prj_name + ''' - the CPU power manager and undervolting tuner with GUI
Detailed usage on github.com/ustcpetergu/Silitune
Set `uv enabled = 1` in ''' + config_file + ''' to enable undervolting options. 
And make sure you have a valid intel-undervolt config file. 
Be careful!
'''


def cmd_cpu(switch, number):
    return 'echo %d > /sys/devices/system/cpu/cpu%d/online' % (switch, number)


def cmd_cpu_check(number):
    return 'cat /sys/devices/system/cpu/cpu%d/online' % number


def cmd_uv_set_uv_get(option):
    def cmd_uv_set_uv_inner(value):
        try:
            val = float(value)
        except ValueError:
            logging.error('Undervolting value invalid!')
            return 'false'
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
        try:
            val = float(value)
        except ValueError:
            logging.error('TDP or Time Window value invalid!')
            return 'false'
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
        runcmd(None, cmd_sync_disk)
        logging.info(runresult(None, cmd_undervolt_read))
    else:
        logging.info("Undervolting not enabled.")


def tempdisable_undervolt(tf):
    if undervolt_enabled:
        global uvsetbtn
        if tf:
            uvsetbtn.setEnabled(False)
            for i in underv_array:
                i.setEnabled(False)
            # set all undervolting values to 0
            for i in underv_array[0:5]:
                runcmd(i, i.cmdset('0'))
            runcmd(None, cmd_undervolt_apply)
            runcmd(None, cmd_sync_disk)
            logging.info(runresult(None, cmd_undervolt_read))
        else:
            uvsetbtn.setEnabled(True)
            for i in underv_array:
                i.setEnabled(True)
            apply_undervolt()
    else:
        logging.info("Undervolting not enabled.")


def benchlog(self, text):
    self.benchlogbox.appendPlainText(text)
    # use this to "refresh" the box and show the text
    self.benchlogbox.setHidden(True)
    self.benchlogbox.setHidden(False)


def do_bench(self):
    is_continue = True
    while is_continue:
        bench_result = runresult(None, cmd_bench_small)
        try:
            cpupercent, onecore, allcore = \
                [int(s) for s in bench_result.splitlines()[-1].split() if s.isdigit()]
        except ValueError:
            cpupercent, onecore, allcore = -1, -1, -1 
        benchlog(self, "\t%d\t\t%d\t\t%d" % (cpupercent, onecore, allcore))
        is_continue = self.ch_b.isChecked()
    self.benching = False


def tabmainsetup(self):
    self.vbox = QVBoxLayout()
    self.vbox.setAlignment(Qt.AlignTop)
    # ----------------------------------------------
    # --------------- basic ------------------------
    # ----------------------------------------------
    # title
    hbtit = QHBoxLayout()
    ltitle = MyQLabel(prj_name + " " + prj_ver)
    # ltitle.setFont(self.boldfont)
    hbtit.addWidget(ltitle)
    hbtit.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hbtit)
    # Help button
    bhelp = MyQButton("Help")
    bhelp.button.clicked.connect(self.showhelp)
    setcolor(bhelp, Qt.green)
    # tlp functions
    btlpbat = MyQCmdButton("tlp bat", "tlp bat")
    btlpac = MyQCmdButton("tlp ac", "tlp ac")
    hchildbox = QHBoxLayout()
    hchildbox.addWidget(bhelp)
    hchildbox.addWidget(btlpbat)
    hchildbox.addWidget(btlpac)
    hchildbox.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hchildbox)
    # Radiobutton for profile switch
    lprofile = MyQLabel("Profile Switch")
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
    hb1.addWidget(rbpower)
    hb1.addWidget(rbbatt)
    hb1.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hb1)
    # CPU Turbo
    hb2 = QHBoxLayout()
    cboxturbo = MyQCheckBox("Disable Turbo", cmd_turbo_no, cmd_turbo_yes, cmd_turbo_get)
    cboxturbo.reinit()
    checkbox_array.append(cboxturbo)
    hb2.addWidget(cboxturbo)
    hb2.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hb2)
    # CPU Cores
    core_label = MyQLabel("CPU Cores")
    self.vbox.addWidget(core_label)
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
    self.vbox.addLayout(hb_core)
    # ----------------------------------------------
    # --------------- undervolting -----------------
    # ----------------------------------------------
    # no undervolting enable button, enable/disable in config file
    # cb_uv = QCheckBox("Enable Undervolting", self)
    # cb_uv.clicked.connect(self.uv_enable)
    # Undervolting (including TDP control)
    core_label = MyQLabelRed("Undervolting Control")
    # core_label.setFont(self.boldfont)
    self.vbox.addWidget(core_label)
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
    self.vbox.addLayout(hbuv1)
    self.vbox.addLayout(hbuv2)
    self.vbox.addLayout(hbuv3)
    self.vbox.addLayout(hbuv4)
    # Undervolting apply button
    global uvsetbtn
    uvsetbtn = QPushButton("Apply Undervolt", self)
    # setcolor(uvsetbtn, Qt.red)
    uvsetbtn.setStyleSheet('QPushButton {color:red;}')
    uvsetbtn.setFont(self.font)
    # uvsetbtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    uvsetbtn.clicked.connect(apply_undervolt)
    if not undervolt_enabled:
        uvsetbtn.setEnabled(False)
    # Undervolting temporary turn to Zeros switch
    uvzero = QCheckBox("Temporary Disable", self)
    uvzero.clicked.connect(tempdisable_undervolt)
    uvzero.setCheckState(False)
    setcolor(uvzero, Qt.red)
    if not undervolt_enabled:
        uvzero.setEnabled(False)
    hbuvctrl = QHBoxLayout()
    hbuvctrl.addWidget(uvsetbtn)
    hbuvctrl.addWidget(uvzero)
    hbuvctrl.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hbuvctrl)

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
    hboxbtm.setAlignment(Qt.AlignLeft)
    self.vbox.addLayout(hboxbtm)

    # finish tab1
    self.tab1.setLayout(self.vbox)


def tabmonsetup(self):
    mbox = QVBoxLayout()
    mbox.setAlignment(Qt.AlignTop)
    # ----------------------------------------------
    # --------------- monitoring -------------------
    # ----------------------------------------------
    # Power Consumption Monitoring, CPU status monitoring
    hboxmon = QHBoxLayout()
    self.ch_mon = QCheckBox("Enable Monitor", self)
    self.ch_mon.clicked.connect(self.monitor_option)
    self.ch_mon.setCheckState(False)
    setcolor(self.ch_mon, Qt.green)
    hboxmon.addWidget(self.ch_mon)
    mbox.addLayout(hboxmon)
    global mon_checkbox
    mon_checkbox = self.ch_mon
    # Data showing area
    for i in range(len(mon_name)):
        lab = MyQLabelGreen(mon_name[i])
        mon_label_array.append(lab)
        le = MyQLEMon()
        mon_array.append(le)
    hbmon0 = QHBoxLayout()
    hbmon0.addWidget(mon_label_array[0])
    hbmon0.addWidget(mon_array[0])
    hbmon1 = QHBoxLayout()
    hbmon1.addWidget(mon_label_array[1])
    hbmon1.addWidget(mon_array[1])
    hbmon2 = QHBoxLayout()
    hbmon2.addWidget(mon_label_array[2])
    hbmon2.addWidget(mon_array[2])
    hbmon3 = QHBoxLayout()
    hbmon3.addWidget(mon_label_array[3])
    hbmon3.addWidget(mon_array[3])
    mbox.addLayout(hbmon0)
    mbox.addLayout(hbmon1)
    mbox.addLayout(hbmon2)
    mbox.addLayout(hbmon3)
    # ----------------------------------------------
    # --------------- Data Acquisition -------------
    # ----------------------------------------------
    daqlabel = MyQLabel("Data Acquisition")
    # daqlabel.setFont(self.boldfont)
    setcolor(daqlabel, Qt.green)
    mbox.addWidget(daqlabel)
    daqbtnbox = QHBoxLayout()
    daqbtnbox.setAlignment(Qt.AlignLeft)
    btnstart = MyQButton("Start")
    btnstart.button.clicked.connect(self.daqstart)
    setcolor(btnstart, Qt.green)
    btnend = MyQButton("End")
    btnend.button.clicked.connect(self.daqend)
    setcolor(btnend, Qt.green)
    btnplot = MyQButton("Plot")
    btnplot.button.clicked.connect(self.daqplot)
    setcolor(btnplot, Qt.green)
    btnsave = MyQButton("Save")
    btnsave.button.clicked.connect(self.daqsave)
    setcolor(btnsave, Qt.green)
    daqbtnbox.addWidget(btnstart)
    daqbtnbox.addWidget(btnend)
    daqbtnbox.addWidget(btnplot)
    daqbtnbox.addWidget(btnsave)
    mbox.addLayout(daqbtnbox)
    self.daqstatus = MyQLabel("No data.")
    self.daqstatus.setWordWrap(True);
    mbox.addWidget(self.daqstatus)

    self.daqrunning = False
    self.daqdata = None

    self.tab2.setLayout(mbox)


def tabbenchsetup(self):
    mbox = QVBoxLayout()
    mbox.setAlignment(Qt.AlignTop)
    # ----------------------------------------------
    # --------------- bench ------------------------
    # ----------------------------------------------
    # this is stable branch, so brutal and normally useless full-benchmark is removed.
    # see dev branch for details.
    b_label = MyQLabel("7z Benchmark")
    mbox.addWidget(b_label)
    hboxb = QHBoxLayout()
    hboxb.setAlignment(Qt.AlignLeft)
    self.ch_b = QCheckBox("Continuous Bench", self)
    self.ch_b.setCheckState(False)
    hboxb.addWidget(self.ch_b)
    bbtn = MyQButton("Start Bench")
    bbtn.button.clicked.connect(self.start_bench)
    hboxb.addWidget(bbtn)
    mbox.addLayout(hboxb)

    self.benching = False

    self.benchlogbox = QPlainTextEdit()
    self.benchlogbox.setReadOnly(True)
    self.benchlogbox.appendPlainText("\tCPU%\t1CoreMIPS\tAllCoreMIPS")
    mbox.addWidget(self.benchlogbox)

    self.tab3.setLayout(mbox)


def tabloggersetup(self):
    # ----------------------------------------------
    # --------------- logger -----------------------
    # ----------------------------------------------
    font = QFont()
    font.setPointSize(8)
    logtextbox = QTextEditLogger(self)
    logtextbox.widget.setFont(font)
    # You can format what is printed to text box
    logtextbox.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:\n %(message)s'))
    logging.getLogger().addHandler(logtextbox)
    # You can control the logging level
    logging.getLogger().setLevel(logging.INFO)
    lgrlayout = QVBoxLayout()
    lgrlayout.addWidget(logtextbox.widget)

    self.tab4.setLayout(lgrlayout)


def tababoutsetup(self):
    abox = QVBoxLayout()
    # ----------------------------------------------
    # --------------- about ------------------------
    # ----------------------------------------------
    lpic = QLabel(self)
    pixmap = QPixmap(image_dir + '/logo.png')
    smaller = pixmap.scaled(self.width-50, self.width-50, Qt.KeepAspectRatio)
    lpic.setPixmap(smaller)
    abox.addWidget(lpic)

    ltitle = MyQLabel(prj_name + " " + prj_ver)
    abox.addWidget(ltitle)
    ltitle = MyQLabel("Licensed under " + prj_license)
    abox.addWidget(ltitle)
    ltitle = MyQLabel("Website: " + prj_website)
    abox.addWidget(ltitle)
    abox.setAlignment(Qt.AlignTop)

    self.tab5.setLayout(abox)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = prj_name
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 700

        # check if dependencies like intel-undervolt is ready
        self.check_dep()
        # Start piling up widgets
        self.font = QFont()
        self.font.setPointSize(14)
        self.boldfont = QFont()
        self.boldfont.setPointSize(14)
        self.boldfont.setBold(True)
        self.setFont(self.font)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tabs.addTab(self.tab1, "Main")
        self.tabs.addTab(self.tab2, "Monitor")
        self.tabs.addTab(self.tab3, "Bench")
        self.tabs.addTab(self.tab4, "Logger")
        self.tabs.addTab(self.tab5, "About")

        tabmainsetup(self)
        tabloggersetup(self)
        tabbenchsetup(self)
        tabmonsetup(self)
        tababoutsetup(self)

        self.threadpool = QThreadPool()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.show()
        # timers: replace multithreading
        self.timermon = QTimer()
        self.timermon.setInterval(update_interval_mon * 1000)
        self.timermon.timeout.connect(self.updatemon)
        self.timermon.start()
        self.on_power_now = -1
        self.timerswitch = QTimer()
        self.timerswitch.setInterval(update_interval_switch * 1000)
        self.timerswitch.timeout.connect(self.updateswitch)
        self.timerswitch.start()

    def check_dep(self):
        if runcmd(self, 'which tlp') != 0:
            QMessageBox.warning(self, '',
                                'tlp executable not found!',
                                QMessageBox.Yes)
        if runcmd(self, 'which intel-undervolt') != 0:
            QMessageBox.warning(self, '',
                                'intel-undervolt executable not found!',
                                QMessageBox.Yes)
        if runcmd(self, 'ls ' + iu_config_file) != 0:
            QMessageBox.warning(self, '',
                                'intel-undervolt configure file not found, undervolt functions may misbehave!',
                                QMessageBox.Yes)

    def showhelp(self):
        QMessageBox.information(self, prj_name + ' Help',
                                help_str,
                                QMessageBox.Yes)

    def monitor_option(self):
        global monitor_enabled
        monitor_enabled = int(self.ch_mon.isChecked())

    def updatemon(self):
        if monitor_enabled and on_front:
            results = []
            tlp1 = runresult(None, 'tlp-stat -t')
            cpu_temp = -273.15
            fan_speed = []
            fan_speed_text = ''
            for lines in tlp1.splitlines():
                if 'CPU temp' in lines:
                    try:
                        cpu_temp = int([s for s in lines.split() if s.isdigit()][0])
                    except IndexError:
                        logging.error("Error getting CPU temperature!")
                if 'Fan speed' in lines:
                    try:
                        fan_speed.append(int([s for s in lines.split() if s.isdigit()][0]))
                    except IndexError:
                        logging.error("Error getting fan speed!")
                        fan_speed.append([-1])
                    fan_speed_text += str(fan_speed[-1]) + ','
            cpu_temp_text = str(cpu_temp) + ' C'
            fan_speed_text = fan_speed_text[:-1] + ' RPM'
            bat_stat = runresult(None, 'cat /sys/class/power_supply/{}/status'.format(batt_name))
            if bat_stat == 'Discharging':
                bat_volt = int(batt_volt)
                # fix for some thinkpad models
                try:
                    os.stat('/sys/class/power_supply/{}/current_now'.format(batt_name))
                    bat_curr = int(runresult(None, 'cat /sys/class/power_supply/{}/current_now'.format(batt_name)))
                    bat_watt = bat_volt * bat_curr / 1000000000000
                except FileNotFoundError:
                    try:
                        os.stat('/sys/class/power_supply/{}/power_now'.format(batt_name))
                        bat_watt = int(runresult(None, 'cat /sys/class/power_supply/{}/power_now'.format(batt_name))) / 1000000
                    except FileNotFoundError:
                        logging.error('not found power_now or current_now, bat watt invalid')
                        bat_watt = 0
                bat_watt_text = '%.2f' % bat_watt
            else:
                bat_watt_text = bat_stat
                bat_watt = -1
            cpu_freqs_orig = runresult(None, 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq')
            cpu_freqs = []
            cpu_freqs_text = ''
            for lines in cpu_freqs_orig.splitlines():
                cpu_freqs.append(int(lines) / 1000)
                cpu_freqs_text += '%d,' % cpu_freqs[-1]
            cpu_freqs_text = cpu_freqs_text[:-1]
            mon_array[0].setText(cpu_temp_text)
            mon_array[1].setText(fan_speed_text)
            mon_array[2].setText(bat_watt_text)
            mon_array[3].setText(cpu_freqs_text)
            if self.daqrunning is True:
                self.daqdata[0].append(readable_time())
                self.daqdata[1].append(cpu_temp)
                self.daqdata[2].append(fan_speed)
                self.daqdata[3].append(bat_watt)
                self.daqdata[4].append(cpu_freqs)

    def updateswitch(self):
        on_power_last = self.on_power_now
        self.on_power_now = on_power()
        if on_power_last != self.on_power_now:
            if self.on_power_now:
                logging.debug("Switch to AC")
                profileswitch_pgm(0)
            else:
                logging.debug("Switch to battery")
                profileswitch_pgm(1)

    def daqstart(self):
        self.daqstatus.setText("Start collecting data...")
        self.daqdata = [[], [], [], [], []]
        self.daqrunning = True

    def daqend(self):
        self.daqstatus.setText("End collecting data...")
        self.daqrunning = False

    def daqplot(self):
        if self.daqdata is None or len(self.daqdata[0]) == 0:
            return
        plt.subplot(221)
        plt.plot(self.daqdata[0], self.daqdata[1])
        plt.title("CPU temp [C]")
        plt.subplot(222)
        for i in range(len(self.daqdata[2][0])):
            plt.plot(self.daqdata[0], [x[i] for x in self.daqdata[2]])
        plt.title("Fan speed(s) [RPM]")
        plt.subplot(223)
        plt.plot(self.daqdata[0], self.daqdata[3])
        plt.title("Battery usage [W]")
        plt.subplot(224)
        for i in range(len(self.daqdata[4][0])):
            plt.plot(self.daqdata[0], [x[i] for x in self.daqdata[4]])
        plt.title("CPU frequencies [MHz]")
        plt.show()
        self.daqstatus.setText("Plot launched.")

    def daqsave(self):
        if self.daqdata is None:
            logging.error("No data!")
            return
        runcmd(None, 'mkdir -p %s' % data_dir)
        filename = data_dir + '/silitune-%s.dat' % readable_time()
        with open(filename, 'w') as f:
            csv.writer(f, delimiter=',').writerows(self.daqdata)
        self.daqstatus.setText("Data saved to %s." % filename)
        return filename

    def start_bench(self):
        if self.benching is False:
            self.benching = True
            t = threading.Thread(name='BenchThread', target=do_bench, args=(self,))
            t.start()

    def notify(self, string="Nope"):
        QMessageBox.information(self, '', string, QMessageBox.Yes)


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None, body=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)
        menu.triggered.connect(self.actions)
        menu.addAction("To Power")
        menu.addAction("To Battery")
        menu.addAction("Re-apply Undervolt")
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
        elif text == 'Re-apply Undervolt':
            apply_undervolt()


if __name__ == '__main__':
    print(prj_name + " started running...")
    if os.getuid() != 0:
        print("Are you r00t?")
        exit(-1)
    app = QApplication(sys.argv)
    init_config()
    ex = App()
    w = QWidget()
    trayIcon = SystemTrayIcon(QIcon(image_dir + "/icon.png"), w, body=ex)
    trayIcon.show()
    app.exec_()
    print("Goodbye.")
    sys.exit(0)
