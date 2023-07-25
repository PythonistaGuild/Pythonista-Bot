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
import textwrap

import discord
from discord.ext import commands, tasks
from discord.utils import MISSING, format_dt

import core


class Logging(commands.Cog):
    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot

        self.user: discord.User | None = MISSING  # none is for a failed fetch

        if url := core.CONFIG["LOGGING"].get("webhook_url"):
            self.webhook = discord.Webhook.from_url(url, session=bot.session, client=bot)
        else:
            bot.log_handler.warning("Not enabling webhook logging due to config key not existing.")
            self.webhook = None

    async def cog_load(self) -> None:
        if self.webhook:
            self.logging_loop.start()

    async def cog_unload(self) -> None:
        if self.webhook:
            self.logging_loop.cancel()

    @tasks.loop(seconds=0)
    async def logging_loop(self) -> None:
        assert self.webhook

        to_log = await self.bot.logging_queue.get()

        attributes = {"INFO": "\U00002139\U0000fe0f", "WARNING": "\U000026a0\U0000fe0f"}

        emoji = attributes.get(to_log.levelname, "\N{CROSS MARK}")
        dt = datetime.datetime.utcfromtimestamp(to_log.created)

        message = textwrap.shorten(f"{emoji} {format_dt(dt)}\n{to_log.message}", width=1990)

        embed = to_log.__dict__.get("embed") or discord.utils.MISSING

        avatar_url: str | None = core.CONFIG["LOGGING"].get("webhook_avatar_url")
        actor_name = "PythonistaBot Logging"

        if not avatar_url and self.user is not None and "runner" in core.CONFIG["LOGGING"]:
            runner_id: int = core.CONFIG["LOGGING"]["runner"]
            try:
                user = self.user or self.bot.get_or_fetch_user(runner_id)
            except:
                self.user = user = None  # This will tell us not to attempt again.

            if user:
                avatar_url = user.display_avatar.url
                actor_name = f"Logging: Dev: {user.display_name}"

        await self.webhook.send(
            message,
            username=actor_name,
            avatar_url=core.CONFIG["LOGGING"].get("webhook_avatar_url"),
            embed=embed,
        )


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Logging(bot))
