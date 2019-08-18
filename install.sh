#!/bin/bash
echo 'SiliTune Installer started...'
if [ $USER != 'root' ]; then
	echo 'You should be root!'
	exit 255
fi
mkdir -pv /etc/silitune
if [ -e /etc/silitune/sili.conf ]; then
	echo 'Old configure file found, do nothing'
else
	echo 'Install configure file'
	cp -v ./sili.conf.sample /etc/silitune/sili.conf
fi
echo 'Install silitune to /usr/local'
mkdir -pv /usr/local/silitune
cp -av ./icon.png ./LICENSE ./README.md ./sililib.py ./silitune.py /usr/local/silitune/
echo 'Install desktop entry'
cp -av ./SiliTune.desktop.template /usr/share/applications/SiliTune.desktop
echo 'Done.'
