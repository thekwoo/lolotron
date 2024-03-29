# External Libraries
from datetime import datetime, timedelta
import disnake
from disnake.ext import commands
import emoji
import re
import textwrap
from typing import Any,Dict,List,Tuple

# Internal Libraries
#import extmessage
import tracker

class rsvp(commands.Cog):
    """ Create event RSVPs.

    RSVPs allow for orderly tracking of sign-ups.
    """

    # Maybe one day we can set this per server in settings...but that requires a bit
    # more work than I'm willing to do right now.
    # Note: This **MUST** be a PartialEmoji or Emoji object otherwise all of the compares
    #       will fall apart
    # For HIDE:
    #rsvpEmoji = discord.PartialEmoji(animated=False, name='nomcookie', id=563107909828083742)
    # For Development:
    #rsvpEmoji = discord.PartialEmoji(animated=False, name='tempest', id=556941054277058560)

    templateMessageBody = \
    '''

    Please react to this message with {} to join.
    Removing your reaction will lose your spot in the queue.

    '''

    # TODO: This specifies that time is always in UTC, which is currently true.
    #       But hopefully it won't always be that way
    templateMessageFoot = \
    '''SystemID: {}\nExpiration Time: {} UTC'''

    expireTimeIncr = timedelta(days=3, hours=0)
    expireTimeExt  = timedelta(days=1, hours=0)
    expireTimeFmt  = '%A %b %d - %H:%M:%S %Z'

    # RegEx to search a message for a line starting with a discord emoji
    emojiRegex = re.compile(r'^(<:(\w*):(\d*)>)')

    def __init__(self, bot, settings):
        self.bot = bot

        self.rsvps = {}

        # Register out callbacks with the reactionTracker
        self.tracker = self.bot.get_cog('reactTracker')
        self.tracker.registerCallbacks(type(self).__name__, self.msgGenerator, self.parseMsg)

        # Create sign-up emoji from settings
        # If we have a user setting for it, use it. Otherwise we use a ":raisedhands:" emoji as a default
        if 'rsvpEmoji' in settings:
            self.rsvpEmoji = disnake.PartialEmoji(animated=False,
                                                  name=settings['rsvpEmoji']['name'],
                                                  id  =settings['rsvpEmoji']['id'])
        else:
            self.rsvpEmoji= disnake.PartialEmoji(animated=False,
                                                name='\U0001F64C')

    '''
    Helper function that generates the RSVP message
    '''
    async def msgGenerator(self, event:tracker.Tracker):
        # Create the main message
        # This is broken up this way to prevent stupid tabs from making indents look weird
        msg = textwrap.dedent(self.templateMessageBody.format(self.rsvpEmoji))

        # First collect the list of valid signups as well as valid reacts to the special reacts
        # To prevent strange shenanigans, the owner is always first regardless if they have
        # the appropriate react or not
        signups = [event.owner]
        sreacts = {}
        for e in event.entries:
            # Ignore invalid entries
            if not e.valid:
                continue

            # Check if this is the signup react
            if e.react == self.rsvpEmoji:
                # Prevent double counting if the owner reacted againg
                if e.user in signups:
                    continue

                signups.append(e.user)
                continue

            # Check if this is a special react
            for r in event.cogData:
                if e.react == r:
                    if e.user in sreacts:
                        sreacts[e.user].append(r)
                    else:
                        sreacts[e.user] = [r]

        # Go through the signup list in order, adding special reacts if applicable
        # Signup list enumeration always starts at 1 for non-programmers
        cnt = 1
        for s in signups:
            msg += '{} - {}'.format(cnt, s.display_name)
            if s in sreacts:
                msg += ' [ '
                for r in sreacts[s]:
                    msg += '{} '.format(r)
                msg += ']'
            msg += '\n'
            cnt += 1

        # Retrieve embed object from the message object
        msgEmbed = event.msgObj.embeds[0]

        # We will delete all fields that are signups and recreate them now
        msgEmbed.clear_fields()

        # Now go through the message we want and break it up by the max field length
        # NOTE: This does not respect maximum embed length and can still fail there
        cMsg = ''
        fieldCnt = 0
        for l in msg.splitlines(keepends=True):
            if len(cMsg + l) > 1024:
                if (fieldCnt == 0):
                    msgEmbed.add_field(name='Sign-ups', value=cMsg, inline=False)
                else:
                    msgEmbed.add_field(name='\u200B', value=cMsg, inline=False)

                cMsg = ''
                fieldCnt += 1

            cMsg += l

        if len(cMsg) > 0:
            if (fieldCnt == 0):
                msgEmbed.add_field(name='Sign-ups', value=cMsg, inline=False)
            else:
                msgEmbed.add_field(name='\u200B', value=cMsg, inline=False)

        await event.msgObj.edit(embed=msgEmbed)

    '''
    Parses a message for emojis that are at the start of the line, indicating that they
    are special
    '''
    def parseMsg(self, event:tracker.Tracker):
        trackedEmojis = []

        for s in iter(event.message.splitlines()):
            # Remove all whitespace at the start of the line
            sStrip = s.lstrip()

            # Search if its a Discord style emoji first
            matchObj = self.emojiRegex.search(sStrip)
            if matchObj is not None:
                tEmoji = disnake.PartialEmoji(animated=False, name=matchObj.group(2), id=int(matchObj.group(3)))

                # Prevent duplicates from making it into the list
                if tEmoji not in trackedEmojis:
                    trackedEmojis.append(tEmoji)
                continue

            # Next try to lookup the emoji by unicode
            # Check to make sure the first character ISNT a normal character since the emoji library's regex
            # will find anything. This check allows us to make sure a unicode emoji is at the start of the line
            # We also need to check for ':' since a unicode emoji may be the name
            if ((len(sStrip) > 0) and (sStrip[0] == ':' or not (sStrip[0].isascii()))):
                matchObj = emoji.emoji_list(sStrip)
                if matchObj is not None:
                    # This only will grab the first emoji in a line. This is by design
                    tEmoji = disnake.PartialEmoji(animated=False, name=matchObj[0]['emoji'], id=None)

                    # Prevent duplicates from making it into the list
                    if tEmoji not in trackedEmojis:
                        trackedEmojis.append(tEmoji)
                    continue

        event.cogData = trackedEmojis

    @commands.group(pass_context=True)
    async def rsvp(self, ctx):
        pass

    @rsvp.command(brief = '''Create a new RSVP event''',
                  help  = '''Create a new RSVP event. All text after the "add" command will be used in the message
                           as is. You can use any basic discord or serer hosted emoji in your text''',
                  usage = '''<title> <msg>''')
    async def add(self, ctx, title, *, msgBody):
        # Get the owner from the context
        owner = ctx.author

        # Create the embed for the message
        # Metadata is located in the footer which we will add later since we don't have the info for it yet
        msg = disnake.Embed()
        msg.title = title
        msg.description = msgBody
        #msg.add_field(name='Details', value=msgBody, inline=False)
        msg.add_field(name='Sign-ups', value='Preparing sign ups...', inline=False)

        msgObj = await ctx.channel.send(embed=msg)

        # Finish setting up the RSVP Event Object
        event = self.tracker.createTrackedItem(msgObj=msgObj, user=owner, msg=msgBody, cogOwner=type(self).__name__)

        # Add footer now that we have the message ID
        msg = msgObj.embeds[0]
        msg.set_footer(text=self.templateMessageFoot.format(event.msgObj.id, event.expire.strftime(self.expireTimeFmt)))
        await msgObj.edit(embed=msg)

        # Search for special emojis
        self.parseMsg(event)

        # Update the RSVP Message from the bot
        await self.msgGenerator(event)

        # For convenience, add the reaction to the post so people don't have to dig it up
        await event.msgObj.add_reaction(self.rsvpEmoji)

        for e in event.cogData:
            await event.msgObj.add_reaction(e)

        print('Created an RSVP with ID {}'.format(event.msgObj.id))

        # Delete the original message now that we're done parsing it
        await ctx.message.delete()

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            print('RSVP Add Failed to convert a passed argument')
            await ctx.send('RSVP Add could not parse out a title and/or new description. ' +
                           'Please check your syntax.\n' +
                           'It should be: add "<title>" <new description>')
        else:
            print(error)

    @rsvp.command(brief = '''Edits an existing RSVP event message.''',
                  help  = '''Edits an existing RSVP event message. Only the owner of the message can edit
                           the message. The entire message is replaced and reparsed during this command.''',
                  usage = '''<systemID> "<title>" <msg>''')
    async def edit(self, ctx, msgId:int, title:str, *, msgBody):
        # Ignore ourselves
        if ctx.author == self.bot.user:
            return

        # Grab the event and make sure we can operate on it
        event = self.tracker.getTrackedItem(msgId)
        if event is None:
            print('RSVP Edit is not tracking anything with ID {}. Skipping...'.format(msgId))
            await ctx.send('RSVP Edit could not find a message that is active with ID {}. Double check your message ID.'.format(msgId))
            return

        ## Only the owner is allowed to edit
        if ctx.author != event.owner:
            print('RSVP Edit was called by {}, who is not the owner ({})'.format(
                ctx.author.display_name,
                event.owner.display_name))
            await ctx.send('RSVP Edit can only be used on messages you own. You are {} but the owner is {}'.format(
                ctx.author.display_name,
                event.owner.display_name))
            return

        # Update the title and details field
        msgObj = event.msgObj
        msgEmbed = msgObj.embeds[0]
        msgEmbed.title = title
        msgEmbed.description = msgBody
        await event.msgObj.edit(embed=msgEmbed)

        # Update Emojis
        event.message = msgBody
        self.parseMsg(event)

        # TODO: There is an edge case here where the edit will remove existing reacts. We currently don't remove
        #       the ones we made ourselves, but we should probably consider it. It gets complicated as we will
        #       need to determine not only that the emoji isn't in the tracked set now, but also that we were
        #       the ones who created it, and then remove it
        for trackedEmoji in event.cogData:
            for react in event.msgObj.reactions:
                if trackedEmoji == react.emoji:
                    break
            else:
                await event.msgObj.add_reaction(trackedEmoji)

        # Update message
        await self.msgGenerator(event)

        # Delete the modifying message
        await ctx.message.delete()

    @edit.error
    async def edit_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            print('RSVP Edit Failed to convert a passed argument')
            await ctx.send('RSVP Edit could not parse out a message ID to delete, title, and/or new description. ' +
                           'Please check your syntax.\n' +
                           'It should be: edit <message ID> "<title>" <new description>')
        else:
            print(error)

    @rsvp.command(brief = '''Deletes an existing RSVP event message.''',
                  help  = '''Deletes an existing RSVP message. Only the owner of the message can delete it.
                             Deletion is permanent and un-recoverable. On completion, the entire history of
                             the message is purged.''',
                  usage = '''<systemID>''')
    async def delete(self, ctx, msgId:int):
        # Ignore ourselves
        if ctx.author == self.bot.user:
            return

        # Look up event
        event = self.tracker.getTrackedItem(msgId)

        # Skip modifying anything if we aren't tracking this message
        if event is None:
            print('RSVP Delete is not tracking anything with ID {}. Skipping...'.format(msgId))
            await ctx.send('RSVP Delete could not find a message that is active with ID {}. Double check your message ID.'.format(msgId))
            return

        # Only the owner is allowed to delete
        if ctx.author != event.owner:
            print('RSVP Delete was called by {}, who is not the owner ({})'.format(
                ctx.author.display_name,
                event.owner.display_name))
            await ctx.send('RSVP Delete can only be used on messages you own. You are {} but the owner is {}'.format(
                ctx.author.display_name,
                event.owner.display_name))
            return

        # Delete the message
        await event.msgObj.delete()
        self.tracker.deleteTrackedItem(msgId)

        # Delete the modifying message to indicate that we've processed it
        await ctx.message.delete()

    @delete.error
    async def delete_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            print('RSVP Delete Failed to convert a passed argument')
            await ctx.send('RSVP Delete could not parse out a message ID to delete. Please check your syntax.\n' +
                            'It should be: delete <message ID>')
        else:
            print(error)

    @rsvp.command(brief = '''Extends the duration of an existing RSVP event message.''',
                  help  = '''Extends the duration of an existing RSVP message. Only the owner of the message can
                             extend it. You can only add additional time, not remove. Extension is a set amount of
                             time (referred to as a time unit) and cannot be adjusted by the user. The quantity
                             provided is the number of time units to extend by.''',
                  usage = '''<systemID> <quantity>''')
    async def extend(self, ctx, msgId:int, qty:int):
        # Ignore ourselves
        if ctx.author == self.bot.user:
            return

        event = self.tracker.getTrackedItem(msgId)

        # Skip modifying anything if we aren't tracking this message
        if event is None:
            print('RSVP Extend is not tracking anything with ID {}. Skipping...'.format(msgId))
            await ctx.send('RSVP Extend could not find a message that is active with ID {}. Double check your message ID.'.format(msgId))
            return

        # Extend the message
        extTime = self.expireTimeExt * qty
        event.expire += extTime

        # We need to edit the footer with the new expiration time
        msgObj = event.msgObj
        msg = msgObj.embeds[0]
        msg.set_footer(text=self.templateMessageFoot.format(event.msgObj.id, event.expire.strftime(self.expireTimeFmt)))
        await msgObj.edit(embed=msg)

        # Reprint the message
        #await self.msgGenerator(event)

        # Delete the modifying message to indicate that we've processed it
        await ctx.message.delete()

    @extend.error
    async def extend_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            print('RSVP Extend Failed to convert a passed argument')
            await ctx.send('RSVP Extend could not parse out a message ID and/or time quantity to extend. Please check your syntax.\n' +
                            'It should be: extend <message ID> <quantity>')
        else:
            print(error)