import asyncio
import discord

TOKEN = ''

client = discord.Client()

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

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await message.channel.send('Message ID: {:d}. Returning what you said: {:s}'.format(message.id, message.content))

@client.event
async def on_reaction_add(reaction, user):
    await reaction.message.channel.send('User {:s} added the following reaction {} to message id {:d}'.format(user.name, reaction.emoji, reaction.message.id))

print('Starting to run')
client.run(TOKEN)
print('Should be done')