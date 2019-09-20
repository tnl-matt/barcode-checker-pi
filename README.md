# Barcode Checker

This is python code to run on a Raspberry Pi with GPIO
pins attached to LEDs.

To run on Raspberry Pi startup, put the command in
startup_entry.txt into /etc/rc.local.

Since this is in /etc/rc.local, it will run as sudo,
so to install:

`sudo pip install requirements.txt`

This only runs on Python 2.7
