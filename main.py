import asyncio
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import discord
import discord.ext.commands as dxc
import json
import sys
import time
from typing import Any,Dict,List,Tuple

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot('%', description='')

# For the RSVP system we need to track events
@dataclass
class rsvpEntry:
    user: discord.user
    timeStamp: datetime
    valid: bool

@dataclass
class rsvpEvent:
    owner: discord.user
    message: str
    rsvps: List[rsvpEntry]
    expire: datetime
    trackId: int

rsvpTracker = {}

rsvpEmoji = '\U0001F64B'
rsvpTemplateMessageBody = \
'''
Posted by: {}
{}

Please react to this message with :raising_hand: to join.
Removing your reaction will lose your spot in the queue.

Signup:
'''

rsvpTemplateMessageFoot = \
'''
Additional Options:
rsvp_delete <SystemID> - to delete this (owner only)
rsvp_audit  <SystemID> - to show entire history
rsvp_ext    <SystemID)
SystemID: {}
Expiration Time: {}
'''

'''
Helper function that generates the RSVP message
'''
def rsvpMsgGenerator(event:rsvpEvent) -> str:
    # Create the header
    msg = rsvpTemplateMessageBody.format(event.owner.display_name, event.message)

    # Iterate through the RSVP list in order, skipping entires that were cancelled
    # Also keep a counter for enumeration, but start with 1 index for non-programmers
    cnt = 1
    for r in event.rsvps:
        if r.valid:
            msg += '{} - {}\n'.format(cnt, r.user.display_name)


    # Append the footer information
    # TODO: The expiration time should be something better than the float, we should format it
    msg += rsvpTemplateMessageFoot.format(event.trackId, event.expire)

    return msg

#rsvpExpireTimeIncr = timedelta(days=1, hours=12)
rsvpExpireTimeIncr = timedelta(seconds=30)

'''
Garbage collector that should be called whenver an event occurs. Will purge the
event list of events that have expired

I can't figure out a better way than for all functions to call this periodically,
so we'll just treat this as a lazy garbage collector.
'''
def rsvpCleanup():
    expiredList = []
    for k,v in rsvpTracker.items():
        if v.expire <= datetime.utcnow():
            print('Found an expired event with id {}'.format(k))
            expiredList.append(k)

    for k in expiredList:
        rsvpTracker.pop(k)

# TODO: Do we even need this
@client.event
async def on_connect():
    print('Connected')

'''
Initial setup to know that things have worked
'''
@client.event
async def on_ready():
    print('*' * 80)
    print('Should be ready to go now.')
    print('I am: {:s}'.format(client.user.name))
    print('*' * 80)

    print('I am connected to the following servers:')
    for g in client.guilds:
        print(g.name)

        for chan in g.text_channels:
            print('--> {:s}'.format(chan.name))

@client.command()
async def rsvp(ctx, *, arg):
    # Run cleanup
    rsvpCleanup()

    # Save off the poster's message
    msgBody = arg
    owner = ctx.author

    # We need to create a message and send it to get a messageID, since we use the messageID as the identifier
    # We will edit the actual content later
    msg = await ctx.channel.send('Preparing an RSVP message...')
    print('The message I just sent has ID {:d}'.format(msg.id))

    # Finish setting up the RSVP Event Object
    timeNow    = datetime.utcnow()
    timeExpire = timeNow + rsvpExpireTimeIncr

    firstEntry          = rsvpEntry(owner, timeNow, True)
    event               = rsvpEvent(owner, msgBody, [firstEntry], timeExpire, msg.id)
    rsvpTracker[msg.id] = event

    # Update the RSVP Message from the bot
    msgTxt = rsvpMsgGenerator(event)
    await msg.edit(content=msgTxt)

    # For convenience, add the reaction to the post so people don't have to dig it up
    await msg.add_reaction(rsvpEmoji)

    # Delete the original message now that we're done parsing it
    await ctx.message.delete()

'''
Adds the user to the list of RSVPs
'''
@client.event
async def on_reaction_add(reaction, user):
    # Run cleanup
    rsvpCleanup()

    # Grab the message ID to see if we should even try to parse stuff
    msgId = reaction.message.id

    # Ignore ourselves
    if user == client.user:
        return

    # Skip modifying anything if we aren't tracking on this message
    if msgId not in rsvpTracker:
        print('could not find {:d} in the tracker so ignoring this'.format(msgId))
        return
    else:
        event = rsvpTracker[msgId]

    # Check that this is the correct
    if rsvpEmoji != reaction.emoji:
        print('reacted emjoi doesnt match expected. got {}'.format(reaction.emoji))
        return

    # Check if the user is already in the list, this should really just be an edge case for the owner
    for r in event.rsvps:
        if (r.user == user) and (r.valid):
            return

    # Add RSVP to the list
    newEntry = rsvpEntry(user, datetime.utcnow(), True)
    event.rsvps.append(newEntry)

    msgTxt = rsvpMsgGenerator(event)
    await reaction.message.edit(content=msgTxt)

'''
Removes the user from the list of RSVPs
'''
@client.event
async def on_raw_reaction_remove(payload):
    # Run cleanup
    rsvpCleanup()

    # We need to go dig through everything to find the message T_T
    # We thankfully can skip looking up the guild and just find the channel ID, which will
    # also cover the cases of private messages
    channel = client.get_channel(payload.channel_id)
    message = await channel.get_message(payload.message_id)
    user    = client.get_user(payload.user_id)
    emoji   = payload.emoji

    # Grab the message ID to see if we should even try to parse stuff
    msgId = message.id

    # Skip modifying anything if we aren't tracking on this message
    if msgId not in rsvpTracker:
        print('could not find {:d} in the tracker so ignoring this'.format(msgId))
        return
    else:
        event = rsvpTracker[msgId]

    # Check that this is the correct
    if rsvpEmoji != emoji.name:
        print('reacted emjoi doesnt match expected. got {}'.format(emoji))
        return

    # Look for the user in the list
    for r in event.rsvps:
        if (r.user == user) and (r.valid):
            rsvp = r
            break
    else:
        # Something goofy happened...so we'll just pretend it never happened
        print('reaction_remove sub-routine failed to find the user who un-reacted.')
        return

    # For auditing's sake, we don't delete entries, only invalidate them
    rsvp.valid = False

    msgTxt = rsvpMsgGenerator(event)
    await message.edit(content=msgTxt)

###############################################################################
# Load General Settings
# We shouldn't store the token in source, and this also provides a way to store
# other bot-wide settings.
###############################################################################
with open('lolotron_config.json', 'r') as f:
    rawSettings = f.read()
    genSettings = json.loads(rawSettings)

token = genSettings['token']

###############################################################################
# Time to start everything. We never return from here, so make sure everything
# is setup above this line
###############################################################################
print('Starting to run')
client.run(token)
print('Should be done')