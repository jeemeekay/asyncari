#!/usr/bin/python3

"""Brief example of using the channel API with a state machine.

This app will answer any channel sent to Stasis(hello), and play "Hello,
world" to the channel. For any DTMF events received, the number is played back
to the channel. Press # to hang up, and * for a special message.
"""

#
# Copyright (c) 2013, Digium, Inc.
#

import trio_ari
from trio_ari.state import ToplevelChannelState
import trio_asyncio
import trio
import logging

import os
ast_url = os.getenv("AST_URL", 'http://localhost:8088/')
ast_username = os.getenv("AST_USER", 'asterisk')
ast_password = os.getenv("AST_PASS", 'asterisk')
ast_app = os.getenv("AST_APP", 'hello')

class State(ToplevelChannelState):
    do_hang = False

    async def on_start(self):
        await self.channel.play(media='sound:hello-world')

    async def on_dtmf_Hash(self, evt):
        self.do_hang = True
        await self.channel.play(media='sound:vm-goodbye')

    async def on_dtmf_Pound(self, evt):
        await self.channel.play(media='sound:asterisk-friend')

    async def on_dtmf(self, evt):
        await self.channel.play(media='sound:digits/%s' % evt.digit)

    async def on_PlaybackFinished(self, evt):
        if self.do_hang:
            await self.channel.continueInDialplan()
        
async def on_start(objs, event, client):
    
    """Callback for StasisStart events.

    On new channels, register the on_dtmf callback, answer the channel and
    play "Hello, world"

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    channel = objs['channel']
    await channel.answer()
    await client.nursery.start(State(channel).run)

async def main():
    async with trio_ari.connect(ast_url, ast_app, ast_username,ast_password) as client:
        client.on_channel_event('StasisStart', on_start, client)
        # Run the WebSocket
        async for m in client:
            print("** EVENT **", m)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        trio_asyncio.run(main)
    except KeyboardInterrupt:
        pass
