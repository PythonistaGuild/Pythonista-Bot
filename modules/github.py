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

import aiohttp
import discord

import core

if TYPE_CHECKING:
    from bot import Bot

GITHUB_ISSUE_URL = "https://github.com/{}/issues/{}"
LIB_ISSUE_REGEX = re.compile(r"(?P<lib>[a-z]+)?##(?P<number>[0-9]+)", flags=re.IGNORECASE)

GITHUB_BASE_URL = "https://github.com/"
GITHUB_RAW_CONTENT_URL = "https://raw.githubusercontent.com/"

aliases = [
    (("wavelink", "wave", "wl"), "PythonistaGuild/Wavelink"),
    (("discordpy", "discord", "dpy"), "Rapptz/discord.py"),
    (("twitchio", "tio"), "TwitchIO/TwitchIO"),
]
LIB_REPO_MAPPING = {key: value for keys, value in aliases for key in keys}


class GitHub(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.code_highlight_emoji = "📃"

    def _strip_content_path(self, url: str) -> str:
        file_path = url[len(GITHUB_BASE_URL):]
        return file_path

    async def format_highlight_block(self, url: str, line_adjustment: int = 10):
        try:
            highlighted_line = int(url.split("#L")[1])  # seperate the #L{n} highlight
        except:
            return None

        file_path = self._strip_content_path(url)
        raw_url = GITHUB_RAW_CONTENT_URL + file_path.replace("blob/", "") # Convert it to a raw user content URL

        code = ""
        async with aiohttp.ClientSession() as session:
            async with session.get(raw_url) as r:
                if r.status == 404:
                    return

                code += await r.text()

        code = code.splitlines()

        code_block_dict = {"lines": {}}
        j = 0
        for i in code:
            # populate the dict
            code_block_dict["lines"][j] = i
            j += 1

        code_block_dict["lines"][j] = "\n"

        line_list = code_block_dict["lines"]

        if highlighted_line - 1 not in line_list:
            return None

        bound_adj = line_adjustment  # adjustment for upper and lower bound display
        _minBoundary = (highlighted_line - 1 - bound_adj)
        _maxBoundary = (highlighted_line - 1 + bound_adj)

        # loop through all the lines, and adjust the formatting
        msg = "```ansi\n"
        key = _minBoundary
        while key <= _maxBoundary:
            currLineNum = str(key + 1)
            # insert a space if there is no following char before the first character...
            if key + 1 == highlighted_line:
                highlighted_msg_format = "\u001b[0;37m\u001b[4;31m{}  {}\u001b[0;0m\n".format(
                    currLineNum, line_list[key]
                )

                msg += highlighted_msg_format
            else:
                display_str = "{}  {}\n" if line_list.get(key) is not None else "" # if we hit the end of the file, just write an empty string
                msg += display_str.format(currLineNum, line_list.get(key))
            key += 1

        msg += "\n```"

        github_dict = {
            "path": file_path,
            "min": _minBoundary if _minBoundary > 0 else highlighted_line,      # Do not display negative numbers if <0
            "max": _maxBoundary,
            "msg": msg
        }
        return github_dict

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

        codeSegment = await self.format_highlight_block(message.content)

        if codeSegment is None:
            return

        await message.add_reaction(self.code_highlight_emoji)

        path = codeSegment['path']
        _min = codeSegment['min']
        _max = codeSegment['max']
        code_fmt = codeSegment['msg']

        def check(reaction, user):
            return reaction.emoji == self.code_highlight_emoji and user != self.bot.user \
                and message.id == reaction.message.id

        await self.bot.wait_for("reaction_add", check=check)

        code_display_msg = await message.channel.send(
            content="Showing lines `{}` - `{}` in: `{}`...\n{}".format(_min, _max, path, code_fmt),
            suppress_embeds=True
        )

        await self.bot.wait_for("reaction_remove", check=check)
        await code_display_msg.delete()

        # clean up reactions
        await message.clear_reactions()


async def setup(bot: Bot) -> None:
    await bot.add_cog(GitHub(bot))
