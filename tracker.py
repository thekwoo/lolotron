from dataclasses import dataclass
from datetime import datetime
import discord
from enum import Enum, auto
from typing import Any,Dict,List,Tuple

'''
These datastructures are for storing tracked items. It is consumer defined
(determined by the trackerType) what do do with the entries within the
tracked item
'''

'''
An enumeration of the possible tracked items
'''
class trackerType(Enum):
    rsvp = auto()
    poll = auto()

'''
An entry in the tracker. These are essentially timestamped reacts. Since discord
does not actually do any real accounting for these, we allow for tracking creation
and removal via the valid field.

Also, since reacts can either be emojis or custom things, we just store the string
representation to make comparisons easier
'''
@dataclass
class trackerEntry:
    user:       discord.user
    react:      discord.Emoji or str
    timeStamp:  datetime
    valid:      bool

'''
A tracked item. This is essentially the message the bot will create, and a list of
reactions to it via the above trackerEntry objects.
'''
@dataclass
class Tracker:
    owner:      discord.user
    message:    str
    entries:    List[trackerEntry]
    expire:     datetime
    trackType:  trackerType
    trackId:    int

'''
Garbage collector that should be called whenever an event occurs. Will purge the
event list of events that have expired

I can't figure out a better way than for all functions to call this periodically,
so we'll just treat this as a lazy garbage collector.
'''
def gc(cList: Dict[int, Tracker]) -> Dict[int, Tracker]:
    expiredList = []
    cTime = datetime.utcnow()

    # Find all the tracking items that are expired
    for k,v in cList.items():
        if v.expire <= cTime:
            print('Found an expired event with id {}'.format(k))
            expiredList.append(k)

    # remove all the expired events
    for k in expiredList:
        cList.pop(k)

    return cList
