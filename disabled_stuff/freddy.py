from util import hook, http, web
from subprocess import check_output, CalledProcessError

@hook.command
def freddycode(inp):
    """freddycode <code> - Check if the Freddy Fresh code is correct."""

    try:
        return "Freddy: '%s' ist %s" % (inp, \
            check_output(["/bin/freddycheck", inp]))
    except CalledProcessError as err:
        return "Freddy: Skript returned %s" % (str(err))

