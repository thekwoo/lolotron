import asyncio
from collections import namedtuple
import discord
import discord.ext.commands as dxc
import json
import sys
import time
from typing import Any,Dict,List,Tuple

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot('%', description='')

# For the RSVP systme we need to track events
rsvpEntry = namedtuple('rsvpEntry', ['user', 'timeStamp', 'valid'])
rsvpEvent = namedtuple('rsvpEvent', ['owner', 'message', 'rsvps', 'expire', 'id'])
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
Helper function that generates the message
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
    msg += rsvpTemplateMessageFoot.format(event.id, event.expire)

    return msg


@client.event
async def on_connect():
    print('Connected')

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
    # Save off the poster's message
    msgBody = arg

    owner = ctx.author
    print('The owner of this message is: {}'.format(owner))


    # We need to create a message and send it to get a messageID, since we use the messageID as the identifier
    # We will edit the actual content later
    msg = await ctx.channel.send('Preparing an RSVP message...')
    print('The message I just sent has ID {:d}'.format(msg.id))

    # Finish setting up the RSVP Event Object
    firstEntry = rsvpEntry(owner, time.time(), True)
    rsvpList = [firstEntry]
    event = rsvpEvent(owner, msgBody, rsvpList, 0.0, msg.id)
    rsvpTracker[msg.id] = event

    # Update the RSVP Message from the bot
    msgTxt = rsvpMsgGenerator(event)
    await msg.edit(content=msgTxt)

    # Delete the original message now that we're done parsing it
    await ctx.message.delete()

#@client.event
#async def on_message(message):
#    # Ignore anything from myself
#    if message.author == client.user:
#        return
#
#    #
#    await message.channel.send('Message ID: {:d}. Returning what you said: {:s}'.format(message.id, message.content))
#

@client.event
async def on_reaction_add(reaction, user):
    # Grab the message ID to see if we should even try to parse stuff
    msgId = reaction.message.id

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
        if r.user == user:
            return

    # Add RSVP to the list
    newEntry = rsvpEntry(user, time.time(), True)
    event.rsvps.append(newEntry)

    msgTxt = rsvpMsgGenerator(event)
    await reaction.message.edit(content=msgTxt)

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