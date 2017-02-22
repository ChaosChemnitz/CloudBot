# -*- coding: utf-8 -*-
from util import hook
import re
import time
import requests
import urllib
from subprocess import check_output
import json
import socket
import struct

def run_ecmd(cmd):
#    baseuri = "http://netio.chch.lan.ffc/ecmd?"
#    baseuri = "http://10.8.128.35/ecmd?"
    baseuri = "http://127.0.0.1:4280/ecmd?"
    cmds = "%20".join(cmd)
    req = requests.get("%s%s" % (baseuri, cmds))
    return req.text.strip()

def run_udp(cmd):
    ip="127.0.0.1"
    port=49152
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 10 ms timeout
    s.settimeout(0.1)
    s.sendto(cmd, (ip, port))
    try:
        rec = s.recvfrom(1024)[0]
    except:
        rec = ""
    s.close()
    print(rec)
    return rec

# lamp_lounge handling
@hook.command("lamp_lounge", autohelp=True)
def cmd_lamp_lounge(inp, reply=None):
    """lamp_lounge color - set the lamp color"""
    args = inp.split(" ")
    if len(args) < 1:
        reply("lamp_lounge color - set the lamp color")
        return

    if len(args[0]) != 6:
        reply("lamp_lounge color - set the lamp color")
        return

    c = "a\x00\x03" + struct.pack('BBB', int(args[0][2:4], 16), int(args[0][0:2], 16), int(args[0][4:6], 16))

    rep = run_udp(c)

    if len(rep) < 3:
        reply("Error: no reply")
        return

    if rep[0] == 'a':
        reply("OK")
    elif rep[0] == 'e':
        reply("error: " + rep[3:])
    else:
        reply("fatal error")

@hook.command("lounge_light_toggle", autohelp=False)
def cmd_ounge_light_toggle(inp, reply=None):
    """toggle lounge light modes"""
    reply(check_output("echo lounge_light_toggle | ssh -q -p 2322 command@127.0.0.1", shell=True).strip("\n").decode("utf-8"))
    

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
    changes = r.json()["query"]["recentchanges"]
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
#    try:
        fd = requests.get('http://www.chaoschemnitz.de/chch.json')
        chch_info = fd.json()
        if 'message' in chch_info['state']:
	    message = chch_info['state']['message']
            if " | " in message:
                message = message.split(" | ", 1)[0]
            else:
	        message = ""

        if chch_info['state']['open']:
	    state = "geöffnet".decode("utf-8")
        else:
	    state = "geschlossen"

        return "%s (%s)" % (state, message)
#        return check_output("sudo /bin/chch-status", shell=True).strip("\n").decode("utf-8")
#    except:
#        return "unbekannt"

@hook.command("status", autohelp=False)
def cmd_status(inp, reply=None):
    """status - Return the door status"""
    reply("Chaostreff Status: %s" % (getstatus()))

@hook.event("TOPIC")
def topic_update(info, conn=None, chan=None):
    print("topic update")
    """topic_update -- Update the topic on TOPIC command"""
    if chan != "#ChaosChemnitz":
        return

    status = getstatus()
    print("status: %s" % (status.encode('utf8')))

    topic = info[-1].split(" | ")
    print("topic: %s" % ([ elem.encode('utf8') for elem in topic ]))

    sstr = "Status: %s" % (status)
    print("sstr: %s" % (sstr.encode('utf8')))
    didset = False
    i = 0
    while i < len(topic):
        if sstr in topic[i]:
            print("Found current status in topic.")
            didset = True
            break
        if 'Status: ' in topic[i]: 
            print("Found Status field in topic.")
            didset = True 
            topic[i] = sstr
        i += 1
    if didset == False:
        print("No topic fiel was found, appending.")
        topic.append(sstr)

    newtopic = " | ".join(topic)
    if newtopic != info[-1]:
        conn.send("TOPIC %s :%s" % (chan, newtopic))

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

