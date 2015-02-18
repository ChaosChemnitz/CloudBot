from util import hook
import re
import time
from subprocess import check_output

def getstatus():
    try:
        return check_output("sudo /bin/chch-status", shell=True).strip("\n").decode("utf-8")
    except:
        return "unbekannt"

@hook.command("status", autohelp=False)
def cmd_status(inp, reply=None):
    """status - Return the door status"""
    reply("Chaostreff Status: %s" % (getstatus()))

@hook.event("TOPIC")
def topic_update(info, conn=None, chan=None):
    """topic_update -- Update the topic on TOPIC command"""
    status = getstatus()

    topic = info[-1]

    sstr = "Status: %s" % (status)
    if sstr in topic:
        return

    if 'Status: ' in topic:
	new_topic = re.sub("Status: [^ ]*", sstr, topic)
    else:
        new_topic = "%s | %s" % (topic.rstrip(' |'), sstr)

    if new_topic != topic:
        conn.send("TOPIC %s :%s" % (chan, new_topic))

@hook.event("332")
def e332_update(info, conn=None, chan=None):
    """e332_update -- run after current topic was requested"""
    chan = info[1]
    topic_update(info, conn=conn, chan=chan)

@hook.singlethread
@hook.event("353")
def e353_update(info, conn=None, chan=None):
    """e353_update -- runs after a channel was joined"""
    chan = info[2]
    if chan.lower() == "#chaoschemnitz":
        conn.send("PRIVMSG Chanserv :op #chaoschemnitz")

    while True:
	conn.send("TOPIC %s" % (chan))
        time.sleep(60)

