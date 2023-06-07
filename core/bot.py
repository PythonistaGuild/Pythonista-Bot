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

import json
import pathlib
from collections import deque
from typing import TYPE_CHECKING, Any

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from .context import Context
from .core import CONFIG
from .utils import LogHandler


if TYPE_CHECKING:
    from asyncio import Queue
    from logging import LogRecord

    import mystbin


class Bot(commands.Bot):
    session: aiohttp.ClientSession
    pool: asyncpg.Pool[asyncpg.Record]
    log_handler: LogHandler
    mb_client: mystbin.Client
    logging_queue: Queue[LogRecord]

    __slots__ = (
        "session",
        "pool",
        "log_handler",
        "mb_client",
        "logging_queue",
        "_previous_websocket_events",
    )

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(CONFIG["prefix"]),
            intents=discord.Intents.all(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self._previous_websocket_events: deque[Any] = deque(maxlen=10)

    async def get_context(
        self, message: discord.Message | discord.Interaction, /, *, cls: type[commands.Context[commands.Bot]] | None = None
    ) -> Context:
        return await super().get_context(message, cls=Context)

    async def on_ready(self) -> None:
        """On Bot ready - cache is built."""
        assert self.user
        self.log_handler.info("Online. Logged in as %s || %s", self.user.name, self.user.id)

    async def on_socket_response(self, message: Any) -> None:
        """Quick override to log websocket events."""
        self._previous_websocket_events.append(message)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        try:
            await super().start(token=token, reconnect=reconnect)
        finally:
            path = pathlib.Path("logs/prev_events.log")

            with path.open("w+", encoding="utf-8") as f:
                for event in self._previous_websocket_events:
                    try:
                        last_log = json.dumps(event, ensure_ascii=True, indent=2)
                    except Exception:
                        f.write(f"{event}\n")
                    else:
                        f.write(f"{last_log}\n")

    async def close(self) -> None:
        """Closes the Bot. It will also close the internal :class:`aiohttp.ClientSession`."""
        await self.session.close()
        await super().close()
