"""MIT License

Copyright (c) 2021-Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from discord.backoff import ExponentialBackoff

import core
from constants import (
    PAPIWebsocketOPCodes,
    PAPIWebsocketCloseCodes,
    PAPIWebsocketNotificationTypes,
    PAPIWebsocketSubscriptions,
)


LOGGER = logging.getLogger(__name__)


WS_URL: str = "wss://api.pythonista.gg/v1/websocket"


class API(core.Cog):
    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot

        self.backoff: ExponentialBackoff = ExponentialBackoff()  # type: ignore
        self.websocket: aiohttp.ClientWebSocketResponse | None = None

        self.connection_task: asyncio.Task[None] | None = None
        self.keep_alive_task: asyncio.Task[None] | None = None

    async def cog_load(self) -> None:
        self.connection_task = asyncio.create_task(self.connect())

    async def cog_unload(self) -> None:
        if self.connection_task:
            try:
                self.connection_task.cancel()
            except Exception as e:
                LOGGER.debug(f'Unable to cancel Pythonista API connection_task in "cog_unload": {e}')

        if self.is_connected():
            assert self.websocket
            await self.websocket.close(code=PAPIWebsocketCloseCodes.NORMAL)

        if self.keep_alive_task:
            try:
                self.keep_alive_task.cancel()
            except Exception as e:
                LOGGER.debug(f'Unable to cancel Pythonista API keep_alive_task in "cog_unload": {e}')

    def is_connected(self) -> bool:
        return self.websocket is not None and not self.websocket.closed

    async def connect(self) -> None:
        token: str | None = core.CONFIG["TOKENS"].get("pythonista")

        if not token:
            self.connection_task = None
            return

        if self.keep_alive_task:
            try:
                self.keep_alive_task.cancel()
            except Exception as e:
                LOGGER.debug(f"Failed to cancel Pythonista API Websocket keep alive. This is likely not a problem: {e}")

        headers: dict[str, str] = {"Authorization": token}

        while True:
            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    self.websocket = await session.ws_connect(url=WS_URL)  # type: ignore
                except Exception as e:
                    if isinstance(e, aiohttp.WSServerHandshakeError) and e.status == 403:
                        LOGGER.critical("Unable to connect to Pythonista API Websocket, due to an incorrect token.")
                        return
                    else:
                        LOGGER.debug(f"Unable to connect to Pythonista API Websocket: {e}.")

                if self.is_connected():
                    session.detach()
                    break
                else:
                    delay: float = self.backoff.delay()  # type: ignore
                    LOGGER.debug(f'Retrying Pythonista API Websocket connection in "{delay}" seconds.')

                    await asyncio.sleep(delay)

        self.connection_task = None
        self.keep_alive_task = asyncio.create_task(self.keep_alive())

    async def keep_alive(self) -> None:
        assert self.websocket

        initial: dict[str, Any] = {
            "op": PAPIWebsocketOPCodes.SUBSCRIBE,
            "subscriptions": [PAPIWebsocketSubscriptions.DPY_MOD_LOG],
        }
        await self.websocket.send_json(data=initial)

        while True:
            message: aiohttp.WSMessage = await self.websocket.receive()

            closing: tuple[aiohttp.WSMsgType, aiohttp.WSMsgType, aiohttp.WSMsgType] = (
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSING,
                aiohttp.WSMsgType.CLOSE,
            )
            if message.type in closing:  # pyright: ignore[reportUnknownMemberType]
                LOGGER.debug(f"Received a CLOSING/CLOSED/CLOSE message type from Pythonista API.")

                self.connection_task = asyncio.create_task(self.connect())
                return

            data: dict[str, Any] = message.json()
            op: int | None = data.get("op")

            if op == PAPIWebsocketOPCodes.HELLO:
                LOGGER.info(f'Received HELLO from Pythonista API: `user={data["user_id"]}`')

            elif op == PAPIWebsocketOPCodes.EVENT:
                subscription: str = data["subscription"]

                if subscription == PAPIWebsocketSubscriptions.DPY_MOD_LOG:
                    self.bot.dispatch("papi_dpy_modlog", data["payload"])

            elif op == PAPIWebsocketOPCodes.NOTIFICATION:
                type_: str = data["type"]

                if type_ == PAPIWebsocketNotificationTypes.SUBSCRIPTION_ADDED:
                    subscribed: str = ", ".join(data["subscriptions"])
                    LOGGER.info(f"Pythonista API added our subscription, currently subscribed: `{subscribed}`")
                elif type_ == PAPIWebsocketNotificationTypes.SUBSCRIPTION_REMOVED:
                    subscribed: str = ", ".join(data["subscriptions"])
                    LOGGER.info(f"Pythonista API removed our subscription, currently subscribed: `{subscribed}`")
                elif type_ == PAPIWebsocketNotificationTypes.UNKNOWN_OP:
                    LOGGER.info(f'We sent an UNKNOWN OP to Pythonista API: `{data["received"]}`')

            else:
                LOGGER.info("Received an UNKNOWN OP from Pythonista API.")


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(API(bot))
