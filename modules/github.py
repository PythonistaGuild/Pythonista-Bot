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

import re
from typing import TYPE_CHECKING

import discord

import core

if TYPE_CHECKING:
    from bot import Bot

GITHUB_ISSUE_URL = "https://github.com/{}/issues/{}"
LIB_ISSUE_REGEX = re.compile(r"(?P<lib>[a-z]+)?##(?P<number>[0-9]+)", flags=re.IGNORECASE)

aliases = [
    (("wavelink", "wave", "wl"), "PythonistaGuild/Wavelink"),
    (("discordpy", "discord", "dpy"), "Rapptz/discord.py"),
    (("twitchio", "tio"), "TwitchIO/TwitchIO"),
]
LIB_REPO_MAPPING = {key: value for keys, value in aliases for key in keys}


class GitHub(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot

    @core.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # Check if we can find a valid issue format: lib##number | ##number
        match = LIB_ISSUE_REGEX.search(message.content)
        if match:
            lib = LIB_REPO_MAPPING.get(match.group("lib"), "PythonistaGuild/Pythonista-Bot")
            issue = match.group("number")

            await message.channel.send(GITHUB_ISSUE_URL.format(lib, issue))


async def setup(bot: Bot) -> None:
    await bot.add_cog(GitHub(bot))
