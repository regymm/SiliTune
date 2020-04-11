# SiliTune - the CPU Power Manager

![](./logo.png)

**WARNING: Use as your own risk! See disclaimer for details!**

You want your laptop CPU works like a beast when your program is being run, and consume as less power as possible when you are on battery just browsing the net. You don't want to open a terminal and type a long command just to disable turbo boost. You don't want to open a terminal and wait for powertop just to see the power consumption.

With this program, you can control your CPU with just a click of mouse, automatically switch management profiles when power cable disconnected/connected, and monitor frequently-used parameters easily. 

A screenshot(A stable -125mV undervolting is quite lucky, not every CPU can get this far): 

![](./screenshot.png)

Functions to be developed:

- [x] Friendly help and document, easy installation, app launcher
- [x] Easy TLP/~~PowerTOP(May cause USB mouse stop responding)~~ toggle
- [x] Enable/disable turbo boost
- [x] Turn on/off CPU cores
- [x] Undervolting and TDP level configuration(by `intel-undervolt`)
- [x] Auto switch profile, ~~handle ACPI events~~, continuous check (per certain seconds) for whether laptop is on AC or battery
- [x] Power consumption monitor, temperature/fan speed/frequency monitor
- [x] system tray icon for easy access and hide
- [x] Multiple tabs for more functions
- [x] Data acquisition & plotting
- [x] Benchmark
- [x] Automatic full benchmark
- [ ] Auto tune(find max Q point)
- [ ] Package in AUR

## A Partial Usage Guide

#### Dependencies

**Required**

Python PyQt5

Python matplotlib

TLP

`intel-undervolt`, available in AUR

`gksu` from gksudo package

**Recommended**

VLC media player for benchmark uses

`7z` for benchmark uses

#### Installation

First, check `install.sh` to see whether there are something wrong, or some files you don't want to override. 

Then run `install.sh` as root to install. 

The program will be installed to `/usr/local/silitune`.

Configure file and desktop launcher will be installed. Old configure file will be untouched. 

#### Configure files

`/etc/silitune/sili.conf` is the place of the main configure file used by silitune, an example can be found at `./sili.conf.example`. The meanings of entries in the file is obvious. The program, instead of you, will deal with it. In most cases you don't need to edit it by yourself. 

One exception: if you want to use the undervolting functions, then you should set `uv enabled = 1` in the `global` section in the configure file manually. 

`/etc/intel-undervolt.conf` and `/etc/intel-undervolt.conf.bak` is changed by the program for undervolting configurations. So backup the file to a name different from these two is recommended. 

#### Launcher

Be careful if you want to let the program auto launch in you desktop environment's settings, I encountered some problems when doing so. 

####  Main Function

The GUI is quite simple to use. 

First, click Help and read it. 

If you don't know the meanings of buttons, like "What's turbo boost?", or "Whether should I change system agent", then you'd better look up before tweaking these options. 

**Options, and Save**

Changed options will have effects immediately(except undervolting settings), but only after pressing `Save config` will those changes written into configure file, or they'll be discarded after quit. 

Power and Battery profiles are not saved simultaneously, so pressing the save button when on power profile will only save your power profile, and vise versa. Considering the mechanism of the program, it's nature to behave like this. 

As an incorrect undervolting may cause system failure, only after pressing the Apply Undervolt button will the undervolting settings be truly written into system. Check twice before press it. Due to my experience, any operation related to undervolting change(like switch profile) may cause system crash, even change from a big value to a small one. 

**Real Real Values**

If you entered an illegal value, or some buttons or options failed to work, the value on the panel will be the (bad) value your assigned, but actually the system is not modified. Press the read real values button will read the (good) values from system, then set them onto the panel. 

**Switch Profile**

The power and battery profiles are switched **automatically** when you connect/disconnect the power cable. And you can also switch by hand. 

**System Tray**

You can always right click the icon in system tray to hide or show the program, and switch profiles quickly. 

#### Monitor & Data Acquisition

Enabled monitor to view CPU, battery and fan information real-time. Monitor will not update if the app is hide to save power. 

Press `Start` and monitor data will be recorded in memory(old ones discarded), press `End` to end. Now the collected data is in RAM: press `Save` will save a plain text dump to (default) `/usr/local/silitune/data`. Press `Plot` to plot these the data in memory via matplotlib, no matter saved or not. 

#### Benchmark

Press `Start Bench` to start a 7zip benchmark, if `Start Again When Finished` is checked, benchmarks will be run one by one, more like a system stress test. Uncheck this if you want benchmark to end. 

`Start Full Evaluation` will do  a series of power consumption and performance tests, including 7z test and VLC video playback test. Place a video named `video.mp4` in your Downloads folder aka `/home/$USER/Downloads/video.mp4` to test. Video longer than 1 minute is recommended. 

Follow the instructions to unplug or plug power cable. 

Please do not touch other options during the benchmark and restart the app when it finished -- this function is currently not very stable! 

After benchmark monitor results and timing details will be saved in `/usr/local/silitune/data`, named like `silitune-######.#.dat` and `silitune-######.#-timing.dat`, in plaintext.  

## Plotter

`plotter.py` can be used to plot saved data and benchmark data. 

Example: `./plotter.py /usr/local/silitune/data/silitune-######.#.dat`

Timing information in timing files will be added if exist. 

## Parameters

Most of the parameters and command names are clearly visible at the top of `silitune.py` -- tune them if you need. 

## Disclaimer

As is shown in the Arch Wiki, undervolting may cause "Instant hardware damage". I'm not responsible for any kind of damage or misbehavior(both you and your computer) caused by this program. 