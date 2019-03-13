import asyncio
from collections import namedtuple
import discord
import discord.ext.commands as dxc
import json
import sys

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot('%', description='')

# For the RSVP systme we need to track events
rsvpEntry = namedtuple('rsvpEntry', ['user'])
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


    msg = await ctx.channel.send('This is an example of me modifying the message.\n' + msgBody)

    print('The message I just sent has ID {:d}'.format(msg.id))

#@client.event
#async def on_message(message):
#    # Ignore anything from myself
#    if message.author == client.user:
#        return
#
#    #
#    await message.channel.send('Message ID: {:d}. Returning what you said: {:s}'.format(message.id, message.content))
#
#@client.event
#async def on_reaction_add(reaction, user):
#    await reaction.message.channel.send('User {:s} added the following reaction {} to message id {:d}'.format(user.name, reaction.emoji, reaction.message.id))


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