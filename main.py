# External Libraries
import asyncio
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import disnake
import disnake.ext.commands as dxc
import json
import sys
import time
from typing import Any,Dict,List,Tuple

# Internal Libraries
import tracker
import rsvp

# Discord is now requiring us to declare the events we want
# This enables the following:
#   guilds, guild_messages, guild_reactions
# The opt in intents are disabled:
#   members, presences
# All other intents are explicity disabled below
clientIntents = disnake.Intents.default()
clientIntents.bans = False
clientIntents.dm_messages = False
clientIntents.dm_reactions = False
clientIntents.dm_typing = False
clientIntents.emojis = False
clientIntents.emojis_and_stickers = False
clientIntents.integrations = False
clientIntents.invites = False
clientIntents.message_content = True
clientIntents.typing = False
clientIntents.voice_states = False
clientIntents.webhooks = False

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot(command_prefix='%', description='', max_messages=None, intents=clientIntents)

# Initial setup to know that things have worked
@client.event
async def on_ready():
    print('*' * 80)
    print('Should be ready to go now.')
    print('I am: {:s}'.format(client.user.name))
    print('*' * 80)

    print('I am connected to the following servers:')
    for g in client.guilds:
        print(g.name)

###############################################################################
# Load General Settings
# We shouldn't store the token in source, and this also provides a way to store
# other bot-wide settings.
###############################################################################
with open('lolotron_config.json', 'r') as f:
    rawSettings = f.read()
    genSettings = json.loads(rawSettings)

token = genSettings['general']['token']

###############################################################################
# Time to start everything. We never return from here, so make sure everything
# is setup above this line
###############################################################################

print('Loading modules')
client.add_cog(tracker.reactTracker(bot=client, settings=genSettings['tracker']))
client.add_cog(rsvp.rsvp(bot=client, settings=genSettings['rsvp']))
print('Starting to run')
client.run(token)
print('Should be done, exiting')