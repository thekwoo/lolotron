import asyncio
from dataclasses import dataclass
from datetime import datetime,timedelta
import discord
from discord.ext import commands
from enum import Enum, auto
from typing import Any,Dict,List,Tuple

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

Fields are as follows:
owner       - The discord user who created this request
message     - The user's message, consumer dependent on how to use this
msgObj      - The discordPy Message object for the message that is being tracked
entries     - A list of trackerEntry which are reactions
expire      - A datetime in UTC for when we will stop tracking this item
msgCallback - A callback function to modify the message based on changes
'''
@dataclass
class Tracker:
    owner:       discord.user
    message:     str
    msgObj:      discord.Message
    entries:     List[trackerEntry]
    expire:      datetime
    msgCallback: Any

'''
A Cog that tracks reactions to a message
'''
class reactTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trackedItems = {}

        bot.loop.create_task(self.gc_task())

    '''
    Creates a tracked object
    '''
    def createTrackedItem(self, msgObj:discord.Message, user:discord.user,
                          msg:str='', callback=None, expire:datetime=None):

        if expire is None:
            expireTime = datetime.utcnow() + timedelta(days=1, hours=12)
        else:
            expireTime = expire

        t = Tracker(user, msg, msgObj, [], expireTime, callback)

        self.trackedItems[msgObj.id] = t
        return t

    '''
    An accessor function to get the tracked object or return None if it
    doesn't exist
    '''
    def getTrackedItem(self, msgId) -> Tracker:
        if msgId not in self.trackedItems:
            return None
        else:
            return self.trackedItems[msgId]

    '''
    An accessor function to safely delete a tracked item before it expires
    This removes the item from being tracked, but does nothing to the message
    itself
    '''
    def deleteTrackedItem(self, msgId):
        try:
            self.trackedItems.pop(msgId)
        except:
            return

    '''
    A task that periodically runs the garbage collector
    '''
    async def gc_task(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            print('Running GC from automated task')
            await self.gc()
            # Sleep until time to run again
            await asyncio.sleep(120)

    '''
    A garbage collection function. This mainly cleans up the tracked list of expired
    events
    '''
    async def gc(self):
        expiredList = []
        cTime = datetime.utcnow()

        # Find all the tracking items that are expired
        for k,v in self.trackedItems.items():
            if v.expire <= cTime:
                print('Found an expired event with id {}'.format(k))
                expiredList.append(k)

        # Remove all the expired events
        for k in expiredList:
            self.trackedItems.pop(k)


    '''
    Adds the user to the list of tracked events
    '''
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore ourselves
        if user == self.bot.user:
            return

        # Run garbage collection so that we don't process expired events
        await self.gc()

        # Grab the message ID to see if we should even try to parse stuff
        msgId = reaction.message.id

        # Skip modifying anything if we aren't tracking on this message
        if msgId not in self.trackedItems:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return
        else:
            event = self.trackedItems[msgId]

        # Check if the user is already in the list, this should really just be an edge case for the owner
        for e in event.entries:
            if (e.user == user) and (e.react == reaction.emoji) and (e.valid):
                return

        # Add RSVP to the list
        newEntry = trackerEntry(user, reaction.emoji, datetime.utcnow(), True)
        event.entries.append(newEntry)

        #debug
        print(event)

        if event.msgCallback is not None:
            await event.msgCallback(event)

    '''
    Removes the user from the list of tracked events
    '''
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # We need to go dig through everything to find the message T_T
        # We thankfully can skip looking up the guild and just find the channel ID, which will
        # also cover the cases of private messages
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.get_message(payload.message_id)
        user    = self.bot.get_user(payload.user_id)
        emoji   = payload.emoji

        # Grab the message ID to see if we should even try to parse stuff
        msgId = message.id

        # Run garbage collection so that we don't process expired events
        await self.gc()

        # Skip modifying anything if we aren't tracking on this message
        if msgId not in self.trackedItems:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return
        else:
            event = self.trackedItems[msgId]

        # Look for the user in the list. Since we are tracking all reacts, we need to
        # compare that it's the same user, emoji, and is the currently active one
        for e in event.entries:
            if (e.user == user) and (e.react == emoji) and (e.valid):
                rsvp = e
                break
        else:
            # Something goofy happened...so we'll just pretend it never happened
            print('reaction_remove sub-routine failed to find the user who un-reacted.')
            return

        # For auditing's sake, we don't delete entries, only invalidate them
        rsvp.valid = False

        # Debug
        print(event)

        # Modify the message
        if event.msgCallback is not None:
            await event.msgCallback(event)