# LoloTron

A Python based Discord automation bot.

## Setup
LoloTron is build on top of [DiscordPy](https://discordpy.readthedocs.io/en/rewrite/index.html) to provide a Python interface to the Discord API.

```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.7
python3.7 --version
git clone https://github.com/thekwoo/lolotron.git
cd lolotron
python3.7 -m pip install -U discord.py
python3.7 -m pip install -U emoji
python3.7 main.py
```

## Running
You simply need to just do:
```
$ python3 main.py
```

Hitting ```ctrl-c``` should eventually stop the process, though it may sometimes require multiple keyboard interrupts to actually stop.
