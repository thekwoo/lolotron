import asyncio
from dataclasses import dataclass
from datetime import datetime,timedelta
import discord
from discord.ext import commands
from enum import Enum, auto
import json
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

    @staticmethod
    def encode(data) -> Dict[str, Any]:
        rtnData = {}

        rtnData['user'] = data.user.id

        if isinstance(data.react, str):
            rtnData['reactType'] = 'unicode'
            rtnData['react'] = data.react
        elif data.react.id is None:
            rtnData['reactType'] = 'unicode'
            rtnData['react'] = data.react.name
        else:
            rtnData['reactType'] = 'emoji'
            rtnData['react'] = data.react.id

        rtnData['timeStamp'] = data.timeStamp.timestamp()
        rtnData['valid']     = data.valid

        return rtnData

    @classmethod
    def decode(cls, client:commands.Bot, data:Dict[str, Any]):
        user  = client.get_user(data['user'])

        if data['reactType'] == 'unicode':
            react = data['react']
        elif data['reactType'] == 'emoji':
            react = client.get_emoji(data['react'])
            if react is None:
                print('Couldnt find emoji with ID {}'.data['react'])
        else:
            react = None

        timeStamp = datetime.fromtimestamp(data['timeStamp'])
        valid = data['valid']

        return trackerEntry(user, react, timeStamp, valid)

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
    msgCallback: str

    @staticmethod
    def encode(data) -> Dict[str, Any]:
        rtnData = {}

        rtnData['owner'] = data.owner.id
        rtnData['msg']   = data.message
        rtnData['msgId'] = data.msgObj.id

        rtnData['entries'] = []
        for e in data.entries:
            rtnData['entries'].append(trackerEntry.encode(e))

        rtnData['expire'] = data.expire.timestamp()
        rtnData['callback'] = data.msgCallback

        return rtnData

    @classmethod
    async def decode(cls, client:commands.Bot, data:Dict[str, Any]):
        print('in decode')
        owner = client.get_user(data['owner'])
        print('owner: {}'.format(owner))
        message = data['msg']
        print('message: {}'.format(message))

        for c in client.get_all_channels():
            for tc in c.text_channels:
                print(tc)
                try:
                    msgObj = await tc.fetch_message(data['msgId'])
                except:
                    continue
                else:
                    break
            else:
                continue

            break
        else:
            msgObj = None
        print("msgObj: {}".format(msgObj))

        entries = []
        for e in data['entries']:
            entries.append(trackerEntry.decode(client, e))
        print("entries: {}".format(entries))

        expire = datetime.utcfromtimestamp(data['expire'])
        print('expire: {}'.format(expire))
        msgCallback = data['callback']

        return Tracker(owner, message, msgObj, entries, expire, msgCallback)


'''
A Cog that tracks reactions to a message
'''
class reactTracker(commands.Cog):
    jsonFileName = 'reactTracker.json'
    def __init__(self, bot):
        self.bot = bot

        self.trackedItems = {}
        self.callbacks = {}

        bot.loop.create_task(self.load_settings())
        bot.loop.create_task(self.gc_task())

    '''
    '''
    def registerCallbacks(self, name, func):
        self.callbacks[name] = func
        print('Callback table is now:')
        print(self.callbacks)

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
    '''
    async def load_settings(self):
        await self.bot.wait_until_ready()

        try:
            with open(self.jsonFileName, 'r') as f:
                jsonData = json.loads(f.read())

            print("read the following data:")
            print(jsonData)
            print('===========================')

            for k,v in jsonData.items():
                print(k)
                print(v)
                t = await Tracker.decode(self.bot, v)
                self.trackedItems[int(k)] = t

        except Exception as e:
            print('loading exception')
            print(e)
            pass

        print(self.trackedItems)


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
                print('GC found an expired event with id {}'.format(k))
                expiredList.append(k)

        # Remove all the expired events
        for k in expiredList:
            self.trackedItems.pop(k)

    '''
    Helper function to compare emojis. Since emojis may be represented as a unicode string,
    a custom emoji (with and ID) or an included emoji (possbily without and id) this function
    tries to figure out what is there and compare accordingly.

    The a parameter should always be a PartialEmoji, but b parameter can be anything emoji like
    '''
    def emojiCompare(self, a:discord.PartialEmoji, b) -> bool:
        if isinstance(b, str):
            return a.name == b
        elif (a.id is not None) and (b.id is not None):
            return a.id == b.id
        else:
            a.name == b.name

    '''
    Adds the user to the list of tracked events
    '''
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # We need to go dig through everything to find the message T_T
        # We thankfully can skip looking up the guild and just find the channel ID, which will
        # also cover the cases of private messages
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user    = self.bot.get_user(payload.user_id)
        emoji   = payload.emoji

        # Ignore ourselves
        if user == self.bot.user:
            return

        # Run garbage collection so that we don't process expired events
        await self.gc()

        # Grab the message ID to see if we should even try to parse stuff
        msgId = message.id

        # Skip modifying anything if we aren't tracking on this message
        if msgId not in self.trackedItems:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return
        else:
            event = self.trackedItems[msgId]

        # Check if the user is already in the list, this should really just be an edge case for the owner
        for e in event.entries:
            if (e.user == user) and (e.react == emoji) and (e.valid):
                print('exiting earlier')
                return

        # Add RSVP to the list
        newEntry = trackerEntry(user, emoji, datetime.utcnow(), True)
        event.entries.append(newEntry)

        #debug
        print(event)

        if (event.msgCallback is not None) and (event.msgCallback in self.callbacks):
            print('Modifying event')
            await self.callbacks[event.msgCallback](event)

    '''
    Removes the user from the list of tracked events
    '''
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # We need to go dig through everything to find the message T_T
        # We thankfully can skip looking up the guild and just find the channel ID, which will
        # also cover the cases of private messages
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
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
            if (e.user == user) and (e.valid) and self.emojiCompare(emoji, e.react):
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
        if (event.msgCallback is not None) and (event.msgCallback in self.callbacks):
            print('Modifying event')
            await self.callbacks[event.msgCallback](event)


    def cog_unload(self):
        print('VVVVVVVVVVVVVVVVVVVVVV')
        try:
            with open(self.jsonFileName, 'w+') as f:
                json.dump(self.trackedItems, f, default=Tracker.encode, indent=4)
        except Exception as e:
            print('got exception')
            print(e)
        print('^^^^^^^^^^^^^^^^^^^^^^')
        print('reactTracker unloading')
        #with open('reactTracker.json', 'w+') as f:
        #    f.write(json.dumps(self.trackedItems, cls=Tracker.encode))