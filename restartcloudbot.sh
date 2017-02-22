#!/bin/bash
cd $(dirname $0)

(
PIDS=""
for i in $(ps -awx | grep -i [c]loudbot | sed "s/^\s*//" | cut -d" " -f1); do
	if [ $i != $$ ]; then
		PIDS="$i $PIDS"
	fi
done
if [ ! -z "$PIDS" ]; then
	kill $PIDS
	sleep 10
	kill -9 $PIDS >/dev/null 2>&1
fi

while true
do
	sudo -u cloudbot ./cloudbot.py 2>&1 | logger -s -t $(basename $0)
	sleep 10
done
) &
disown $!
