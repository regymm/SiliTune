#!/bin/bash
echo 'SiliTune Uninstaller started...'
if [ $USER != 'root' ]; then
	echo 'You should be root!'
	exit 255
fi

rm -vf /usr/bin/silitune
rm -vf /usr/share/applications/silitune.desktop
rm -vrf /usr/lib/silitune

echo 'Main files removed.'
echo 'Please run rm -vf /etc/silitune.conf manually to remove config file'
echo 'Please run rm -vrf /var/lib/silitune manually to remove saved data'
echo 'Done. '
