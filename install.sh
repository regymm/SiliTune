#!/bin/bash
echo 'SiliTune Installer started...'
if [ $USER != 'root' ]; then
	echo 'You should be root!'
	exit 255
fi

# TODO: Detect components
# - intel-undervolt (built with build-essential)
# - tlp
# - vlc
# - p7zip-full
# - python3-pyqt5 python3-matplotlib

if [ -e /etc/silitune/sili.conf ]; then
	echo 'Old configure file found, do nothing'
else
	echo 'Install configure file'
	install -D ./sili.conf.sample /etc/silitune/sili.conf
fi
echo 'Install silitune to /usr/local'
install -t /usr/local/silitune/ ./icon.png ./logo.png ./LICENSE ./README.md ./sililib.py ./silitune.py
echo 'Install desktop entry'
install -D ./SiliTune.desktop.template /usr/share/applications/SiliTune.desktop
echo 'Done.'
