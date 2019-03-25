# External Libraries
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import textwrap
from typing import Any,Dict,List,Tuple

# Internal Libraries
import tracker

class rsvp(commands.Cog):
    # Globals?
    rsvpEmoji = '\U0001F64B'
    templateMessageBody = \
    '''
    Posted by: {}
    {}

    Please react to this message with :raising_hand: to join.
    Removing your reaction will lose your spot in the queue.

    Signup:
    '''

    templateMessageFoot = \
    '''
    ---------------------------------------------
    SystemID: {}
    Expiration Time: {}
    '''

    #expireTimeIncr = timedelta(days=1, hours=12)
    expireTimeIncr = timedelta(seconds=30)

    def __init__(self, bot):
        self.bot = bot

        self.rsvps = {}

    '''
    Helper function that generates the RSVP message
    '''
    def msgGenerator(self, event:tracker.Tracker) -> str:
        # Create the header
        msg = textwrap.dedent(self.templateMessageBody.format(event.owner.display_name, event.message))

        # Iterate through the RSVP list in order, skipping entires that were cancelled
        # Also keep a counter for enumeration, but start with 1 index for non-programmers
        cnt = 1
        for e in event.entries:
            if (e.valid) and (e.react == self.rsvpEmoji):
                msg += '{} - {}\n'.format(cnt, e.user.display_name)


        # Append the footer information
        msg += textwrap.dedent(self.templateMessageFoot.format(event.trackId, event.expire))

        return msg

    '''
    Just a group container that acts as a wrapper as well
    '''
    @commands.group(pass_context=True)
    async def rsvp(self, ctx):
        if ctx.invoked_subcommand is None:
            print('Should do some help here?')

    @rsvp.command()
    async def add(self, ctx, *, arg):
        # Run cleanup
        self.rsvps = tracker.gc(self.rsvps)

        # Save off the poster's message
        msgBody = arg
        owner = ctx.author

        # We need to create a message and send it to get a messageID, since we use the messageID as the identifier
        # We will edit the actual content later
        msg = await ctx.channel.send('Preparing an RSVP message...')
        print('The message I just sent has ID {:d}'.format(msg.id))

        # Finish setting up the RSVP Event Object
        timeNow    = datetime.utcnow()
        timeExpire = timeNow + self.expireTimeIncr

        firstEntry          = tracker.trackerEntry(owner, self.rsvpEmoji, timeNow, True)
        event               = tracker.Tracker(owner, msgBody, [firstEntry], timeExpire,
                                              tracker.trackerType.rsvp, msg.id)
        self.rsvps[msg.id] = event

        # Update the RSVP Message from the bot
        msgTxt = self.msgGenerator(event)
        await msg.edit(content=msgTxt)

        # For convenience, add the reaction to the post so people don't have to dig it up
        await msg.add_reaction(self.rsvpEmoji)

        # Delete the original message now that we're done parsing it
        await ctx.message.delete()

    @rsvp.command()
    async def edit(self, ctx, *, arg):
        print('I am in edit')

    '''
    Adds the user to the list of RSVPs
    '''
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Run cleanup
        self.rsvps = tracker.gc(self.rsvps)

        # Ignore ourselves
        if user == self.bot.user:
            return

        # Grab the message ID to see if we should even try to parse stuff
        msgId = reaction.message.id

        # Skip modifying anything if we aren't tracking on this message
        if msgId not in self.rsvps:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return
        else:
            event = self.rsvps[msgId]

        # Check if the user is already in the list, this should really just be an edge case for the owner
        for r in event.entries:
            if (r.user == user) and (r.react == reaction.emoji) and (r.valid):
                return

        # Add RSVP to the list
        newEntry = tracker.trackerEntry(user, reaction.emoji, datetime.utcnow(), True)
        event.entries.append(newEntry)

        msgTxt = self.msgGenerator(event)
        await reaction.message.edit(content=msgTxt)


        #debug
        print(event)

    '''
    Removes the user from the list of RSVPs
    '''
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Run cleanup
        self.rsvps = tracker.gc(self.rsvps)

        # We need to go dig through everything to find the message T_T
        # We thankfully can skip looking up the guild and just find the channel ID, which will
        # also cover the cases of private messages
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.get_message(payload.message_id)
        user    = self.bot.get_user(payload.user_id)
        emoji   = payload.emoji

        # Grab the message ID to see if we should even try to parse stuff
        msgId = message.id

        # Skip modifying anything if we aren't tracking on this message
        if msgId not in self.rsvps:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return
        else:
            event = self.rsvps[msgId]

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

        msgTxt = self.msgGenerator(event)
        await message.edit(content=msgTxt)