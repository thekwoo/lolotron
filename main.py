# External Libraries
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

# Internal Libraries
import rsvp

# We need to create the client early so that we can override a lot of the functions
# internally. This version is the Bot version so we have access to command parsing
client = dxc.Bot('%', description='')

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

print('Loading modules')
client.add_cog(rsvp.rsvp(client))
print('Starting to run')
client.run(token)
print('Should be done')