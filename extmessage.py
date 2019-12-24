import asyncio
import discord
import math
from typing import Any,List,Dict,Tuple

class ExtMessage():
    # This is the string to use to make a seemingly blank message
    BLANK_STR = '_ _'

    # This is the maximum length of a Discord Message
    MAX_MSG_LEN = 2000

    def __init__(self, msgCnt:int=4, msgRsv:int=2, msg:str=''):
        self.msg    = msg
        self.msgObjs= []

        # See how many messages are required
        # We take the larger of the requested count or the message plus the reserved amount (to account)
        # for growth
        reqMessages = math.ceil(len(self.msg) / self.MAX_MSG_LEN)

        if ((reqMessages + msgRsv) > msgCnt):
            self.msgCnt = reqMessages + msgRsv
        else:
            self.msgCnt = msgCnt

        # The ID will eventually be a message ID, but since it hasn't been created yet
        # we set it to -1 to denote that it is invalid
        self.id = -1

    def splitMessageLine(self, msg:str, length:int=None) -> List[str]:
        # Set the split length to the message default unless it has been specified
        if length is None:
            length = self.MAX_MSG_LEN

        splitMsg = []
        newStr = ''

        # Break the line here is it would run over the limit
        for w in msg.split():
            if ((len(newStr) + len(w) + 1) > self.MAX_MSG_LEN):
                splitMsg.append(newStr)
                newStr = ''

            newStr += w + ' '
        else:
            splitMsg.append(newStr)

        return splitMsg

    def splitMessage(self) -> List[str]:
        # Create blank messages based on how many messages we need to return
        splitMsg = []
        for _ in range(self.msgCnt):
            splitMsg.append('')

        # We first will try to split the message just by newlines and hope that this fits well
        msgSplitByLine = self.msg.splitlines(keepends=True)

        # Make sure none of the split lines are too big
        # If the line is too long, we break it up to the limits
        newMsgSplitByLine = []
        for m in msgSplitByLine:
            if (len(m) > self.MAX_MSG_LEN):
                newMsgSplitByLine.extend(self.splitMessageLine(m))
            else:
                newMsgSplitByLine.append(m)

        # Allocate lines to the messages. Be greedy and try to fill from the top rather than
        # evenly across them
        i = 0
        for m in newMsgSplitByLine:
            # Check if we have room in this message, or need to move onto the next message
            if (len(splitMsg[i]) + len(m) > self.MAX_MSG_LEN):
                # If this was the last message, raise an error
                if (i+1 == self.msgCnt):
                    raise ValueError('Out of characters across all messages for message')
                else:
                    i+=1

            splitMsg[i] += m

        # Fill all unused messages with blank strings
        for i in range(self.msgCnt):
            if (splitMsg[i] == ''):
                splitMsg[i] = self.BLANK_STR

        return splitMsg 

    async def create(self, channel):
        # Get all the messages we need
        messages = self.splitMessage()

        # Create the number of messages needed and store their objects
        for i in range(self.msgCnt):
            self.msgObjs.append(await channel.send(messages[i]))

        # The last object's ID is our ID
        self.id = self.msgObjs[-1].id
    
    async def edit(self, content:str):
        # Make sure the new message is not too long
        msgLen = len(content)
        maxChars = self.msgCnt * self.MAX_MSG_LEN
        if (msgLen > maxChars):
            raise ValueError('New message of length {} is larger than max that can represented {}') 

        # Store the message, then reparse to prepare for editing
        self.msg = content
        messages = self.splitMessage()

        # Edit each message
        # We compare the contents to the new strings and only edit if they differ. This is less for performance
        # than to try to save the "edited" tag on the blank messages
        for i in range(self.msgCnt):
            if (self.msgObjs[i].content != messages[i]):
                await self.msgObjs[i].edit(content=messages[i])

    async def delete(self, delay=None):
        # Delete each message
        for i in range(self.msgCnt):
            await self.msgObjs[i].delete(delay=delay)

        # Clear variables and IDs in case this object gets reused
        self.msgObjs = []
        self.id = -1

    async def publish(self):
        raise NotImplementedError()

    async def pin(self):
        raise NotImplementedError()

    async def unpin(self):
        raise NotImplementedError()

    @property
    def reactions(self):
        return self.msgObjs[-1].reactions

    async def add_reaction(self, emoji):
        # Only add reactions to the last message in the chain
        await self.msgObjs[-1].add_reaction(emoji)

    async def remove_reaction(self, emoji):
        # There should only be reactions on the last message in the chain
        await self.msgObjs[-1].remove_reaction(emoji)

    async def clear_reactions(self):
        # There should only be reactions on the last message in the chain
        await self.msgObjs[-1].clear_reactions()

    async def clean_reactons(self):
        # Clears all reacts except on the last message
        for m in self.msgObjs[:-1]:
            await m.clear_reactions()

    def check_ids(self, id:int) -> bool:
        for m in self.msgObjs:
            if m.id == id:
                return True
        
        return False
        

        