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

import datetime
import json
import pathlib
import sys
import textwrap
import traceback
from collections import deque
from typing import TYPE_CHECKING, Any

import aiohttp
import asyncpg
import discord
from discord.ext import commands
from discord.ext.commands.cog import Cog  # type: ignore # stubs

from constants import GUILD_ID

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

    async def add_cog(self, cog: Cog, /, *, override: bool = False) -> None:  # type: ignore
        # we patch this since we're a single guild bot.
        # it allows for guild syncing only.
        return await super().add_cog(cog, override=override, guild=discord.Object(id=GUILD_ID))

    async def on_ready(self) -> None:
        """On Bot ready - cache is built."""
        assert self.user
        self.log_handler.info("Online. Logged in as %s || %s", self.user.name, self.user.id)

    async def on_socket_response(self, message: Any) -> None:
        """Quick override to log websocket events."""
        self._previous_websocket_events.append(message)

    async def on_error(self, event_name: str, /, *args: Any, **kwargs: Any) -> None:
        exc_type, exception, traceback_ = sys.exc_info()

        if isinstance(exception, commands.CommandInvokeError):
            return

        embed = discord.Embed(title="Event Error", colour=discord.Colour.random())
        embed.add_field(name="Event", value=event_name)

        traceback_text = "".join(traceback.format_exception(exc_type, exception, traceback_))

        embed.description = f"```py\n{traceback_text}\n```"
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

        args_str = ["```py"]
        for index, arg in enumerate(args):
            args_str.append(f"[{index}]: {arg!r}")
            args_str.append("```")
            embed.add_field(name="Args", value="\n".join(args_str), inline=False)

        self.log_handler.error("Event Error", extra={"embed": embed})

    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:  # type: ignore # weird narrowing
        assert ctx.command  # wouldn't be here otherwise

        if not isinstance(error, (commands.CommandInvokeError, commands.ConversionError)):
            return

        error = getattr(error, "original", error)
        if isinstance(error, (discord.Forbidden, discord.NotFound)):
            return

        embed = discord.Embed(title="Command Error", colour=0xCC3366)
        embed.add_field(name="Name", value=ctx.command.qualified_name)
        embed.add_field(name="Author", value=f"{ctx.author} (ID: {ctx.author.id})")

        fmt = f"Channel: {ctx.channel} (ID: {ctx.channel.id})"
        if ctx.guild:
            fmt = f"{fmt}\nGuild: {ctx.guild} (ID: {ctx.guild.id})"

        embed.add_field(name="Location", value=fmt, inline=False)
        embed.add_field(name="Content", value=textwrap.shorten(ctx.message.content, width=512))

        exc = "".join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
        embed.description = f"```py\n{exc}\n```"
        embed.timestamp = discord.utils.utcnow()

        self.log_handler.error("Command Error", extra={"embed": embed})

    async def get_or_fetch_user(
        self,
        target_id: int,
        /,
        *,
        guild: discord.Guild | None = None,
        cache: dict[int, discord.User | discord.Member] | None = None,
    ) -> discord.User | discord.Member | None:
        if guild:
            user = guild.get_member(target_id)
            if not user:
                try:
                    user = await guild.fetch_member(target_id)
                except discord.HTTPException:
                    return

            if cache:
                cache[target_id] = user
            return user

        user = self.get_user(target_id)
        if not user:
            try:
                user = await self.fetch_user(target_id)
            except discord.HTTPException:
                return

        if cache:
            cache[target_id] = user

        return user

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
