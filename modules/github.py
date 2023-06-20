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
import re

import discord

import core


GITHUB_ISSUE_URL = "https://github.com/{}/issues/{}"
LIB_ISSUE_REGEX = re.compile(r"(?P<lib>[a-z]+)?##(?P<number>[0-9]+)", flags=re.IGNORECASE)
GITHUB_CODE_REGION_REGEX = re.compile(
    r"https?://github\.com/(?P<user>.*)/(?P<repo>.*)/blob/(?P<hash>[a-zA-Z0-9]+)/(?P<path>.*)/(?P<file>.*)(?:\#L)(?P<linestart>[0-9]+)(?:-L)?(?P<lineend>[0-9]+)?"
)

GITHUB_BASE_URL = "https://github.com/"
GITHUB_RAW_CONTENT_URL = "https://raw.githubusercontent.com/"

aliases = [
    (("wavelink", "wave", "wl"), "PythonistaGuild/Wavelink"),
    (("discordpy", "discord", "dpy"), "Rapptz/discord.py"),
    (("twitchio", "tio"), "TwitchIO/TwitchIO"),
]

LIB_REPO_MAPPING = {key: value for keys, value in aliases for key in keys}


class GitHub(core.Cog):
    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot
        self.code_highlight_emoji = "📃"
        self.highlight_timeout = 10

    def _strip_content_path(self, url: str) -> str:
        file_path = url[len(GITHUB_BASE_URL) :]
        return file_path

    async def format_highlight_block(self, url: str, line_adjustment: int = 10) -> dict[str, str | int] | None:
        match = GITHUB_CODE_REGION_REGEX.search(url)

        if not match:
            return

        try:
            highlighted_line = int(match["linestart"])  # separate the #L{n} highlight
        except IndexError:
            return

        file_path = self._strip_content_path(url)
        raw_url = GITHUB_RAW_CONTENT_URL + file_path.replace("blob/", "")  # Convert it to a raw user content URL

        code = ""
        async with self.bot.session.get(raw_url) as resp:
            if resp.status == 404:
                return

            code += await resp.text()

        code = code.splitlines()
        code_block_dict: dict[str, dict[int, str]] = {"lines": {}}

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
        _min_boundary = highlighted_line - 1 - bound_adj
        _max_boundary = highlighted_line - 1 + bound_adj

        # get the file extension to format nicely
        file = match["file"]
        extension = file.split(".")[1]

        msg = f"```{extension}\n"
        key = _min_boundary

        max_digit = len(str(_max_boundary))

        # loop through all our lines
        while key <= _max_boundary:
            curr_line_no: str = str(key + 1)
            spaced_line_no = f"%{max_digit}d" % int(curr_line_no)

            # insert a space if there is no following char before the first character...
            if key + 1 == highlighted_line:
                highlighted_msg_format = f">{spaced_line_no}  {line_list[key]}\n"
                msg += highlighted_msg_format

            else:
                # if we hit the end of the file, just write an empty string
                display_str = " {}  {}\n" if line_list.get(key) is not None else ""
                curr_line_no = spaced_line_no
                msg += display_str.format(curr_line_no, line_list.get(key))

            key += 1

        msg += "\n```"

        github_dict = {
            "path": file_path,
            "min": _min_boundary if _min_boundary > 0 else highlighted_line,  # Do not display negative numbers if <0
            "max": _max_boundary,
            "msg": msg,
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

        code_segment = await self.format_highlight_block(message.content)

        if code_segment is None:
            return

        await message.add_reaction(self.code_highlight_emoji)

        path = code_segment["path"]
        _min = code_segment["min"]
        _max = code_segment["max"]
        code_fmt = code_segment["msg"]

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                reaction.emoji == self.code_highlight_emoji and user != self.bot.user and message.id == reaction.message.id
            )

        try:
            await self.bot.wait_for("reaction_add", check=check, timeout=self.highlight_timeout)

            msg: str = f"Showing lines `{_min}` - `{_max}` in: `{path}`...\n{code_fmt}"
            await message.channel.send(msg, suppress_embeds=True)

        except asyncio.TimeoutError:
            return


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(GitHub(bot))
