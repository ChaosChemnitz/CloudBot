#!/bin/bash
cd $(dirname $0)

(
while true
do
	sudo -u cloudbot ./cloudbot.py 2>&1 | logger -s -t $(basename $0)
	sleep 10
done
) &
disown $!
