from util import hook, http, web
from subprocess import check_output, CalledProcessError
from datetime import datetime

@hook.command("bw", autohelp=False)
def bw(inp):
    """bw - list last bandwidth measurement to the outside."""

    try:
	o = check_output("/bin/chch-bandwidth")
    except CalledProcessError as err:
        return "chch-bandwidth: returned %s" % (str(err))

    os = o.split(",")
    upl = int(os[-1])/1024.0/1024.0
    dl = int(os[-2])/1024.0/1024.0
    ts = os[0]
    tsd = datetime.strptime(ts, "%Y%m%d%H%M%S")

    return "%s: upl = %f Mbit/s; dl = %f Mbit/s;" % (tsd, upl, dl)

