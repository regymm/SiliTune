#!/bin/bash
echo 'SiliTune Installer started...'
if [ $USER != 'root' ]; then
	echo 'You should be root!'
	exit 255
fi

# TODO: Detect components
# - intel-undervolt (built with build-essential)
# - tlp
# - python3-pyqt5 python3-matplotlib
# - (optional) p7zip-full

if [ -e /etc/silitune.conf ]; then
	echo 'Old configure file found, do nothing'
else
	echo 'Install configure file'
	install -D ./silitune.conf /etc/silitune.conf
fi
echo 'Install silitune'
install -D -m755 ./silitune.py /usr/bin/silitune
install -d /usr/share/applications /usr/lib/silitune /var/lib/silitune
install -D ./silitune.desktop /usr/share/applications/silitune.desktop
install -D ./icon.png ./logo.png ./sililib.py ./plotter.py /usr/lib/silitune/
echo 'Done.'
