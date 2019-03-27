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

    expireTimeIncr = timedelta(days=1, hours=12)

    def __init__(self, bot):
        self.bot = bot

        self.rsvps = {}
        self.tracker = self.bot.get_cog('reactTracker')

    '''
    Helper function that generates the RSVP message
    '''
    async def msgGenerator(self, event:tracker.Tracker):
        # Create the header
        msg = textwrap.dedent(self.templateMessageBody.format(event.owner.display_name, event.message))

        # Iterate through the RSVP list in order, skipping entires that were cancelled
        # Also keep a counter for enumeration, but start with 1 index for non-programmers
        cnt = 1
        for e in event.entries:
            if (e.valid) and (e.react == self.rsvpEmoji):
                msg += '{} - {}\n'.format(cnt, e.user.display_name)

        # Append the footer information
        msg += textwrap.dedent(self.templateMessageFoot.format(event.msgObj.id, event.expire))

        await event.msgObj.edit(content = msg)

    '''
    Just a group container that acts as a wrapper as well
    '''
    @commands.group(pass_context=True)
    async def rsvp(self, ctx):
        if ctx.invoked_subcommand is None:
            print('Should do some help here?')

    @rsvp.command()
    async def add(self, ctx, *, msgBody):
        # Get the owner from the context
        owner = ctx.author

        # We need to create a message and send it to get a messageID, since we use the messageID as the identifier
        # We will edit the actual content later
        msg = await ctx.channel.send('Preparing an RSVP message...')

        # Finish setting up the RSVP Event Object
        t = self.tracker.createTrackedItem(msg, owner, msg=msgBody, callback=self.msgGenerator)
        firstEntry = tracker.trackerEntry(owner, self.rsvpEmoji, datetime.utcnow(), True)
        t.entries.append(firstEntry)

        # Update the RSVP Message from the bot
        await self.msgGenerator(t)

        # For convenience, add the reaction to the post so people don't have to dig it up
        await t.msgObj.add_reaction(self.rsvpEmoji)

        # Delete the original message now that we're done parsing it
        await ctx.message.delete()

    @rsvp.command()
    async def edit(self, ctx, *, arg):
        # Ignore ourselves
        if ctx.author == self.bot.user:
            return

        # Split the arguments, the first should be the message ID and the second is the string
        # that will become the message
        splitArg = arg.split('\n', 1)

        # If we only got 1 thing, it might be all on the same line, so now break it up by spaces
        if len(splitArg) == 1:
            splitArg = splitArg[0].split(' ', 1)

        if len(splitArg) > 0:
            msgId = int(splitArg[0])
        else:
            print('RSVP Edit did not get a message ID, so we cant do anything. Skipping...')
            return

        if len(splitArg) > 1:
            msg = splitArg[1]
        else:
            msg = None

        # Skip modifying anything if we aren't tracking on this message
        event = self.tracker.getTrackedItem(msgId)
        if msgId is None:
            print('could not find {:d} in the tracker so ignoring this'.format(msgId))
            return

        ## Only the owner is allowed to edit
        if ctx.author != event.owner:
            print('the called {} is not the owner {}'.format(ctx.author.display_name, event.owner.display_name))
            return

        ## Update message
        event.message = msg
        await self.msgGenerator(event)

        ## Delete the modifying message
        await ctx.message.delete()

    @rsvp.command()
    async def delete(self, ctx, arg):
        ## Ignore ourselves
        if ctx.author == self.bot.user:
            return

        try:
            msgId = int(arg)
        except:
            print('Failed to convert rsvp delete argument to delete. Got {}'.format(arg))
            return

        ## Skip modifying anything if we aren't tracking this message
        event = self.tracker.getTrackedItem(msgId)
        if msgId is None:
            print('Could not find {:d} in the tracker so ignoring this'.format(msgId))
            return

        ## Only the owner is allowed to delete
        if ctx.author != event.owner:
            print('Delete called by {} but is not the owner {}'.format(ctx.author.display_name, event.owner.display_name))
            return

        ## Delete the message
        await event.msgObj.delete()
        self.tracker.deleteTrackedItem(msgId)

        ## Debug
        print(self.rsvps)

        ## Delete the modifying message
        await ctx.message.delete()

    @rsvp.command()
    async def extend(self, ctx, arg):
        pass
