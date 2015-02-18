#!/bin/sh

cd $(dirname $0)
while /bin/true;
do
	sudo -u cloudbot ./cloudbot.py
	sleep 10
done

