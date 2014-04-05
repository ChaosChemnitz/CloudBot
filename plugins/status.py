from util import hook
import re

@hook.event("TOPIC")
def topic_update(info, conn=None, chan=None):
    """topic_update -- adds status to topic"""

    # retrieve current status
    status = 'Offen'

    topic = info[1]

    if 'Status' in topic:
        new_topic = re.sub('Status: \w*', 'Status: {}'.format(status), topic)
    else:
        new_topic = topic.rstrip(' |') + ' | Status: {}'.format(status)

    if new_topic != topic:
        out = "TOPIC {} :{}".format(chan, new_topic)
        conn.send(out)
