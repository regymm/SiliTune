# SiliTune - the CPU Power Manager

**WARNING: Use as your own risk. Get prepared to see your laptop on fire or freeze.**

You want your laptop CPU works like a beast when your program is being run, and consume as less power as possible when you are on battery just browsing the net. You don't want to open a terminal and type a long command just to disable turbo boost. 

With this program, you can control your CPU with just a click of mouse, and automatically switch management profiles when power cable disconnected/connected. 

Functions to be developed:

- [x] Enable/disable turbo boost
- [x] Turn on/off CPU cores
- [ ] Undervolting (by `intel-undervolt`)
- [ ] TDP level configuration (by `intel-undervolt`)
- [x] Auto switch profile, ~~handle ACPI events~~, continuous check (per certain seconds) for whether laptop is on AC or battery
- [x] Easy TLP/~~PowerTOP(May cause USB mouse stop responding)~~ toggle
- [ ] Power consumption monitor, temperature/frequency monitor
- [ ] Easy installation
- [x] App launcher, auto start(depends on desktop environment)
- [x] system tray icon for toggle

This project use `intel-undervolt` for undervolting and other CPU tweaks(like temperature and TDP level), `intel-undervolt` is available in AUR.

