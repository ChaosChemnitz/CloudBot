# -*- coding: utf-8 -*-
from util import hook
import re
import time
import requests
import urllib
from subprocess import check_output
import json

def run_ecmd(cmd):
#    baseuri = "http://netio.chch.lan.ffc/ecmd?"
    baseuri = "http://10.8.128.35/ecmd?"
    cmds = "%20".join(cmd)
    req = requests.get("%s%s" % (baseuri, cmds))
    return req.text.strip()

# Lamp handling
@hook.command("lamp", autohelp=True)
def cmd_lamp(inp, reply=None):
    """lamp color [mode] - set the lamp color"""
    args = inp.split(" ")
    if len(args) < 1:
        reply("""lamp color [mode] - set the lamp color""")
        return

    if len(args[0]) != 6:
        reply("""lamp color [mode] - set the lamp color""")
        return

    cmode = "s"
    if len(args) > 1:
        if args[1] == "s" or args[1] == "y" or args[1] == "f":
            cmode = args[1]

    c = []
    c.append([5, int(args[0][0:2], 16)])
    c.append([4, int(args[0][2:4], 16)])
    c.append([3, int(args[0][4:6], 16)])

    for ce in c:
        res = run_ecmd(["channel", str(ce[0]), str(ce[1]), cmode])
        if res != "OK":
             return
    reply("OK")

@hook.command("lamp_fadestep", autohelp=True)
def cmd_lamp_fadestep(inp, reply=None):
    """lamp_fadestep step - set the lamp fadestep"""
    args = inp.split(" ")

    if len(args) < 1:
        reply("""lamp_fadestep step - set the lamp fadestep""")
        return

    reply(run_ecmd(["fadestep", args[0]]))

@hook.command("lamp_fadestep_get", autohelp=False)
def cmd_lamp_fadestep_get(inp, reply=None):
    """lamp_fadestep_get - get the lamp fadestep"""
    reply(run_ecmd(["fadestep"]))

@hook.command("lamp_channels", autohelp=False)
def cmd_lamp_channels(inp, reply=None):
    """lamp_chanels - get the lamp channel count"""
    reply(run_ecmd(["channels"]))

# Wiki handling
def wiki_changes(cmd=False):
    tmpfile = "/tmp/wikichanges.timestamp.txt"
    basewikiuri = "https://www.chaoschemnitz.de/index.php?title=%s"
    wikiapiuri = "https://www.chaoschemnitz.de/api.php?"\
        "action=query&list=recentchanges&format=json&"\
        "rcprop=user|userid|comment|parsedcomment|timestamp|"\
        "title|sha1|sizes|redirect|loginfo|tags|flags"\
        "&rclist=edit|external|new|log"

    try:
        fdch = open(tmpfile, "rw")
        timestamp = fdch.read()
        fdch.close()
    except IOError:
        timestamp = None

    try:
        r = requests.get(wikiapiuri, verify=False)
    except:
        return []

    rarr = []
    changes = r.json["query"]["recentchanges"]
    ntimestamp = changes[0]["timestamp"]
    for change in changes:
        if change["timestamp"] == timestamp:
            break
        uri = basewikiuri % (urllib.quote(change["title"].encode("utf-8"), safe=""))
        rarr.append("wiki: %s changed '%s' ( %s ) comment: %s" %\
            (change["user"], change["title"], uri,\
             change["comment"].strip("\r\n\t")))

    if cmd == False:
        fdch = open(tmpfile, "w+")
        fdch.write("%s" % (ntimestamp))
        fdch.close()

    return rarr

def print_wiki_changes(info, conn=None, chan=None):
    """print_wiki_changes - print wiki changes, when the worker calls"""
    ch = wiki_changes(cmd=False)
    if len(ch) == 0:
        return
    for c in ch[::-1]:
        conn.msg("#chaoschemnitz", c)
        time.sleep(0.5)

@hook.command("wikichanges", autohelp=False)
def cmd_wikichanges(inp, reply=None):
    """wikichanges - Return new recent wiki changes"""
    ch = wiki_changes(cmd=True)
    if len(ch) == 0:
        reply("No changes since the last call were made to the wiki.")
    else:
        for c in ch[::-1][-4:]:
            reply(c)
            time.sleep(0.5)

# Status handling
def getstatus():
    try:
	response = urllib.urlopen('https://www.chaoschemnitz.de/chch.json')
	chch_json = response.read()
	chch_info = json.loads(chch_json)
	if chch_info['state']['open']:
        	return "geöffnet".decode("utf-8")
	else:
        	return "geschlossen"
#        return check_output("sudo /bin/chch-status", shell=True).strip("\n").decode("utf-8")
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

@hook.event("JOIN")
def handle_join(info, input=None, conn=None):
    conn.ctcp(input.nick, "VERSION", "")

@hook.event("NOTICE")
def handle_ctcp_rply(info, input=None, conn=None, nick=None):
    if input.lastparam == "\1%s\1" % "mIRC v7.22 Khaled Mardam-Bey":
        for chan in conn.channels:
            conn.send("KICK %s %s :bad version" % (chan, nick))

@hook.event("332")
def e332_update(info, conn=None, chan=None):
    """e332_update -- run after current topic was requested, runs worker tasks too"""
    chan = info[1]
    topic_update(info, conn=conn, chan=chan)
    print_wiki_changes(info, conn=conn, chan=chan)

@hook.singlethread
@hook.event("353")
def e353_update(info, conn=None, chan=None):
    """e353_update -- runs after a channel (#chaoschemnitz) was joined"""
    chan = info[2]
    if chan.lower() == "#chaoschemnitz":
        conn.send("PRIVMSG Chanserv :op #chaoschemnitz")

    while True:
        time.sleep(60)
	conn.send("TOPIC %s" % (chan))

