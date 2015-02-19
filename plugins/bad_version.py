# -*- coding: utf-8 -*-
from util import hook
from thread import start_new_thread
from time import sleep

def wait_and_send(conn, wait, msg):
    sleep(wait)
    conn.send(msg)

@hook.command("check")
def check_nick(inp, conn=None):
    conn.send("PRIVMSG %s :\x01VERSION\x01" % inp)


@hook.event("JOIN")
def handle_join(info, input=None, conn=None):
    start_new_thread(wait_and_send, (conn, 5, "PRIVMSG %s :\x01VERSION\x01" % input.nick))

@hook.event("NOTICE")
def handle_ctcp_rply(info, input=None, conn=None, nick=None):
    print "notice..."
    print "-%s-" % input.lastparam
    if input.lastparam == ("\1VERSION %s\1" % "mIRC v7.22 Khaled Mardam-Bey"):
        for chan in conn.channels:
            if chan != "#logbot":
                conn.send("KICK %s %s :bad version" % (chan, nick))
                conn.send("MODE %s +b %s!*@*$#logbot" % (chan, nick))

