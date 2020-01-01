import asyncio
import discord
import math
from typing import Any,List,Dict,Tuple

class ExtMessage():
    # This is the string to use to make a seemingly blank message
    BLANK_STR = '_ _'

    # This is the maximum length of a Discord Message
    MAX_MSG_LEN = 2000

    # Special Block Delimiters
    CODE_BLOCK = '```'

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

        # Break down the line into phrases
        # We use whitespace as the delimiter to break a line up into words. Start building new lines word by
        # word until they are just below the maximum line length, or if we're out of words
        # Note: This breaks down if there are no spaces in the message to split on
        for word in msg.split():
            # Couldn't split the line down below the length
            # TODO: Can be drastic here and try to reduce it to max characters at the expense of breaking
            #       a word in half
            if (len(word) > length):
                raise ValueError('splitMessageLine cannot split {} down further, but the result is larger than the max of {}'.format(
                    word, length))

            # Append the new maximally length line to the output as adding this word would exceed the max
            if ((len(newStr) + len(word) + 1) > length):
                splitMsg.append(newStr)
                newStr = ''

            # Add the word to the line
            newStr += word + ' '
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

        msgSplitByLine = newMsgSplitByLine

        # There are a few special multiline blocks we may need to handle.
        # The following are currently supported is discord:
        # Code  Blocks: ``` / ```
        # Quote Blocks: >>>
        # Spoiler Tags:  || / ||
        # We will only try to handle code blocks. The other two are too much of a pain to try
        # to parse unless someone really wants them.
        # To keep the block together, we will aggregate them into a single line "entry". Be aware
        # that this can push it beyond the max length for poorly formed messages. We will just
        # raise an exception rather than trying to rehandle it and insert multiple block entries
        newMsgSplitByLine = []
        inBlock = False
        for m in msgSplitByLine:
            # For code blocks, there can be multiple states where the code block starts/ends are in the same line. We end
            # the lines bit by bit
            if self.CODE_BLOCK in m:
                remainingMsg = m
                while (remainingMsg != ''):
                    # Consume the start of the line before the block starts
                    # Also start creating the aggregated block line with just the block start
                    if ((not inBlock) and (self.CODE_BLOCK in remainingMsg)):
                        blockPos = remainingMsg.find(self.CODE_BLOCK)

                        if (remainingMsg[:blockPos] != ''):
                            newMsgSplitByLine.append(remainingMsg[:blockPos])

                        newStr       = self.CODE_BLOCK
                        remainingMsg = remainingMsg[blockPos + len(self.CODE_BLOCK):]
                        inBlock = True
                    # In the block, and the end block is in the same line
                    elif ((inBlock) and (self.CODE_BLOCK in remainingMsg)):
                        blockPos = remainingMsg.find(self.CODE_BLOCK) + len(self.CODE_BLOCK)
                        newStr  += remainingMsg[:blockPos]

                        # The aggregated block can end up larger than the max character limit
                        # This is a sanity check, but this doesn't actually fix anything
                        if (len(newStr) > self.MAX_MSG_LEN):
                            raise ValueError('Aggregated code block length ({}) exceeds MAX_MSG_LEN ({})'.format(
                                len(newStr), self.MAX_MSG_LEN))

                        # Add the block to it's own line
                        newMsgSplitByLine.append(newStr)

                        remainingMsg = remainingMsg[blockPos:]
                        inBlock = False
                    # In the block and no end of the block
                    elif (inBlock):
                        newStr += remainingMsg
                        remainingMsg = ''
                    # Not in block and no start of block
                    else:
                        if (remainingMsg[:blockPos] != ''):
                            newMsgSplitByLine.append(remainingMsg)

                        remainingMsg = ''

            # We are in a block and there are no end markers
            elif inBlock:
                newStr += m

            # We are not in a block
            else:
                newMsgSplitByLine.append(m)

        msgSplitByLine = newMsgSplitByLine

        # Allocate lines to the messages.
        # If there are less lines than messages try to fill from the bottom so that the text
        # is closest to the message with reactions. Otherwise, greedily fill the messages from
        # top to bottom
        msgIdx = 0
        for lineIdx,line in enumerate(msgSplitByLine):
            while True:
                remainingLines = len(msgSplitByLine) - lineIdx
                remainingMsgs  = self.msgCnt - msgIdx

                # To ensure later messages always have content, make sure there is excess content
                # before we take one for this message
                if (remainingLines >= remainingMsgs):
                    break
                else:
                    msgIdx += 1

            # Check if we have room in this message, or need to move onto the next message
            if (len(splitMsg[msgIdx]) + len(line) > self.MAX_MSG_LEN):
                # If this was the last message, raise an error
                if (remainingMsgs == 0):
                    raise ValueError('Out of characters across all messages for message')
                else:
                    msgIdx += 1

            splitMsg[msgIdx] += line

        # Fill all unused messages with blank strings
        # This will also detect if a line is just whitespace and insert the blank string so that
        # discord won't be annoyed at sending an "empty" message
        for msg in range(self.msgCnt):
            if ((splitMsg[msg] == '') or splitMsg[msg].isspace()):
                splitMsg[msg] += self.BLANK_STR

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

    async def clean_reactions(self):
        # Clears all reacts except on the last message
        for m in self.msgObjs[:-1]:
            await m.clear_reactions()

    def check_ids(self, id:int) -> bool:
        for m in self.msgObjs:
            if m.id == id:
                return True

        return False


