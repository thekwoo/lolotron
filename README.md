# LoloTron

A Python based Discord automation bot.

## Setup
LoloTron is build on top of [DiscordPy](https://discordpy.readthedocs.io/en/rewrite/index.html) to provide a Python interface to the Discord API. Unfortunately, they're in the process of rewriting and it's broken with the PIP version for Python 3.7. To get around this (and other fun issues) you should install from the `rewrite` branch.

    $ git clone https://github.com/Rapptz/discord.py
    $ cd discord.py
    $ python3 -m pip install -U ./