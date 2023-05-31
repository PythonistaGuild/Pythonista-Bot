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
import json
import pathlib
from collections import deque
from typing import Any

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from core import CONFIG
from core.context import Context
from core.utils.logging import LogHandler
from modules import EXTENSIONS


class Bot(commands.Bot):
    session: aiohttp.ClientSession
    pool: asyncpg.Pool[asyncpg.Record]
    log_handler: LogHandler

    __slots__ = (
        "session",
        "pool",
        "log_handler",
    )

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(CONFIG["prefix"]),
            intents=discord.Intents.all(),
        )
        self._previous_websocket_events: deque[Any] = deque(maxlen=10)

    async def get_context(self, message: discord.Message | discord.Interaction) -> Context:
        return await super().get_context(message, cls=Context)

    async def on_ready(self) -> None:
        """On Bot ready - cache is built."""
        assert self.user
        print(f"Online. Logged in as {self.user.name} || {self.user.id}")

    async def on_socket_response(self, message: Any) -> None:
        """Quick override to log websocket events."""
        self._previous_websocket_events.append(message)

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

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


async def main() -> None:
    async with Bot() as bot, aiohttp.ClientSession() as session, asyncpg.create_pool(
        dsn=CONFIG["DATABASE"]["dsn"]
    ) as pool, LogHandler() as handler:
        bot.session = session
        bot.pool = pool
        bot.log_handler = handler

        await bot.load_extension("jishaku")
        for extension in EXTENSIONS:
            await bot.load_extension(extension.name)
            bot.log_handler.log.info(
                "Loaded %sextension: %s",
                "module " if extension.ispkg else "",
                extension.name,
            )

        await bot.start(CONFIG["TOKENS"]["bot"])
