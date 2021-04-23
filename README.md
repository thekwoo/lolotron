# LoloTron
A Python based Discord automation bot for tracking reactions. On top of this reaction tracker are consumers that organize the reactions. Currently, the supported consumers are:
- ```rsvp```: Tracks event sign-ups in order and can include tracking "extra" react

## Setup
Lolotron is built with Python. It requires Python version 3.9+.

### Dependecy Installation
[DiscordPy](https://github.com/Rapptz/discord.py) to provide a Python interface to the Discord API. The last tested version of DiscordPy was 1.7.1.

[Emoji](https://pypi.org/project/emoji/) provides regex for detecting various forms of emojis. The last tested version of Emoji was 1.2.0.

```
py -m pip install -U discord.py
py -m pip install -U emoji
```

### Bot Installation
```
git clone https://github.com/thekwoo/lolotron.git
cd lolotron
```

## Configuration
All settings are contained in ```lolotron_config.json``` for easy modification. There is a section for each component of the bot. Each section is defined as a dictionary.

### general
The general section defines global bot settings. The only value is ```token``` which should be the Discord Bot token.

### tracker
There are no settings for the tracker at this time. Leave this section blank.

### rsvp
This section configures the RSVP component of the bot. The following fields are available:

```rsvpEmoji```: This is a dictionary defining the sign-up emoji to use. If this is not present, a default emoji will be used. It should contain entries for ```name``` and ```id``` used to recreate the sign-up emoji.

## Running
You simply need to just do:
```
py main.py
```

You may need to modify your python invocation command for your particular platform.

Hitting ```ctrl-c``` should eventually stop the process, though it may sometimes require multiple keyboard interrupts to actually stop.

## Usage
### RSVP
The RSVP module provides a means of tracking sign-ups for events and optionally tracking other reacts for those sign-ups.

For example, I have an event that requires some volunteers for particular roles.

### Command Reference
```rsvp add```

Adds an event with ```title``` and ```description```. Note the quotes around ```title``` are required to differentiate it from the ```description```.
```
%rsvp add "<title>" <description>
```

The description will be parsed for special reactions if desired. To indicate that a react is special, you should place the emoji at the start of a line. You can put any description afterwards, the only requirement is that the emoji is at the start. The emoji **must** be one on the server (not from another) and **must not** be animated. Built in emojis are also valid.

The sign-up emoji (based on the server setting) and the special reactions will all be added to the post once parsed. Users must react with the sign-up emoji to be put on the list, and then any number of special reactions can be placed next to their name.

```rsvp edit```

Edits an existing event with the given ```systemId```. Will replace the event title with ```title``` and the description with ```description```. All special reacts will be reparsed and the sign-ups updated accordingly (either additions or deletions). Only the owner of the event can edit the event.
```
%rsvp edit <systemId> "<title>" <description>
```

```rsvp delete```

Deletes an event with the given ```systemId```. Only the owner of the event can delete the event.
```
%rsvp delete <systemId>
```

```rsvp extend```

Extends the expiration of an event with the given ```systemId```. The extension is a multiple of the fixed duration based on the server settings. The multiple is based on the ```quantity``` value. For instance, if the server is set to extend on a 3 hour interval, setting a ```quantity``` of 3 will extend the expiration of the event by 9 hours. Only the owner of the event can extend the event.

```
%rsvp extend <systemId> <quantity>
```