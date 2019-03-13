import asyncio
from collections import namedtuple
import discord
import discord.ext.commands as dxc
import json
import sys
import time

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot('%', description='')

# For the RSVP systme we need to track events
rsvpEntry = namedtuple('rsvpEntry', ['user', 'timeStamp'])
rsvpEvent = namedtuple('rsvpEvent', ['owner', 'message', 'rsvps', 'expire'])
rsvpTracker = {}

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

    msg = await ctx.channel.send('This is an example of me modifying the message.\n' + msgBody)

    firstEntry = rsvpEntry(owner, time.time())
    rsvpList = [firstEntry]

    print('The message I just sent has ID {:d}'.format(msg.id))

    event = rsvpEvent(owner, msgBody, rsvpList, None)
    rsvpTracker[msg.id] = event


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

    # Grab information about the event
    reactEmjoi = reaction.emoji

    # Check if the user is already in the list, this should really just be an edge case for the owner
    for r in event.rsvps:
        if r.user == user:
            return

    # Add RSVP to the list
    newEntry = rsvpEntry(user, time.time())
    event.rsvps.append(newEntry)

    print('New event list:')
    print(event.rsvps)

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