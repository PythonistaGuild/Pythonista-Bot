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
from enum import Enum

import discord

import constants
import core

GITHUB_ISSUE_URL = "https://github.com/{}/issues/{}"
LIB_ISSUE_REGEX = re.compile(r"(?P<lib>[a-z]+)?(?P<pounds>#{2,})(?P<number>[0-9]+)", flags=re.IGNORECASE)
GITHUB_CODE_REGION_REGEX = re.compile(
    r"https?://github\.com/(?P<user>.*)/(?P<repo>.*)/blob/(?P<hash>[a-zA-Z0-9]+)/(?P<path>.*)/(?P<file>.*)(?:\#L)(?P<linestart>[0-9]+)(?:-L)?(?P<lineend>[0-9]+)?",
)

GITHUB_BASE_URL = "https://github.com/"
GITHUB_RAW_CONTENT_URL = "https://raw.githubusercontent.com/"


class LibEnum(Enum):
    wavelink = "PythonistaGuild/Wavelink"
    twitchio = "PythonistaGuild/TwitchIO"
    pythonistaBot = "PythonistaGuild/PythonistaBot"
    mystbin = "PythonistaGuild/Mystbin"
    discordpy = "rapptz/discord.py"


aliases = [
    (("wavelink", "wave", "wl"), LibEnum.wavelink),
    (("discordpy", "discord", "dpy"), LibEnum.discordpy),
    (("twitchio", "tio"), LibEnum.twitchio),
    (("mystbin", "mb"), LibEnum.mystbin),
    (("pythonistabot", "pb"), LibEnum.pythonistaBot),
]

LIB_REPO_MAPPING = {key: value for keys, value in aliases for key in keys}


class GitHub(core.Cog):
    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot
        self.code_highlight_emoji = "📃"
        self.bruhkitty = "<:bruhkitty:710507405347389451>"
        self.highlight_timeout = 10

    def _strip_content_path(self, url: str) -> str:
        return url[len(GITHUB_BASE_URL) :]

    async def format_highlight_block(self, url: str, line_adjustment: int = 10) -> dict[str, str | int] | None:
        match = GITHUB_CODE_REGION_REGEX.search(url)

        if not match:
            return None

        try:
            highlighted_line = int(match["linestart"])  # separate the #L{n} highlight
        except IndexError:
            return None

        file_path = self._strip_content_path(url)
        raw_url = GITHUB_RAW_CONTENT_URL + file_path.replace("blob/", "")  # Convert it to a raw user content URL

        code = ""
        async with self.bot.session.get(raw_url) as resp:
            if resp.status == 404:
                return None

            code += await resp.text()

        code = code.splitlines()
        code_block_dict: dict[str, dict[int, str]] = {"lines": {}}

        line_start = match["linestart"]
        line_end = match["lineend"]

        bulk = False  # are we highlighting a specific block of code?

        line_start = int(line_start)
        line_end = int(line_end) if line_end is not None else 0

        if line_end != 0:
            bulk = True

        j = 0
        for i in code:
            # populate the dict
            code_block_dict["lines"][j] = i
            j += 1

        code_block_dict["lines"][j] = "\n"
        line_list = code_block_dict["lines"]

        if highlighted_line - 1 not in line_list:
            return None

        bound_adj = line_adjustment  # adjustment for upper and lower bound display.
        min_boundary = highlighted_line - 1 - bound_adj if bulk is False else line_start - 1
        max_boundary = highlighted_line - 1 + bound_adj if bulk is False else line_end - 1

        # is our minimum greater than our maximum?
        if min_boundary > max_boundary:
            # re-arrange the variables so we get the proper min - max scale
            min_ = min_boundary
            max_ = max_boundary

            min_boundary = max_
            max_boundary = min_

        # get the file extension to format nicely
        file = match["file"]
        extension = file.rsplit(".")[-1]

        msg = f"```{extension}\n"
        key = min_boundary

        max_digit = len(str(max_boundary))

        # loop through all our lines
        while key <= max_boundary:
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

        path = match["path"]
        file_path = f"{path}/{file}"

        return {
            "path": file_path,
            "min": (min_boundary if min_boundary > 0 else highlighted_line - 1) + 1,  # Do not display negative numbers if <0
            "max": max_boundary + 1,
            "msg": msg,
        }

    def _smart_guess_lib(self, msg: discord.Message) -> LibEnum | None:
        # this is mostly the same as the function in manuals.py
        # however the enum is entirely different so the code isn't reusable.
        assert msg.channel

        if msg.channel.id == constants.Channels.HELP_CHANNEL:
            return None  # there's not much hope here, stay quick

        if isinstance(msg.channel, discord.Thread) and msg.channel.parent_id == constants.Channels.HELP_FORUM:
            tags = {x.name for x in msg.channel.applied_tags}

            if "twitchio-help" in tags:
                return LibEnum.twitchio
            if "wavelink-help" in tags:
                return LibEnum.wavelink
            if "discord.py-help" in tags:
                return LibEnum.discordpy

            return None

        if msg.channel.id == constants.Channels.WAVELINK_DEV:
            return LibEnum.wavelink
        if msg.channel.id == constants.Channels.TWITCHIO_DEV:
            return LibEnum.twitchio

        return None

    @core.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # Check if we can find a valid issue format: lib##number | ##number
        match = LIB_ISSUE_REGEX.search(message.content)
        if match and len(match.group("pounds")) == 2:
            lib = LIB_REPO_MAPPING.get(match.group("lib"), None)

            if not lib:
                lib = self._smart_guess_lib(message)

            if lib:  # no, this should not be an else, as lib can be reassigned in the previous block
                issue = match.group("number")

                await message.channel.send(GITHUB_ISSUE_URL.format(lib.value, issue))

            else:
                await message.add_reaction(self.bruhkitty)

        code_segment = await self.format_highlight_block(message.content)

        if code_segment is None:
            return

        await message.add_reaction(self.code_highlight_emoji)

        path = code_segment["path"]
        min_ = code_segment["min"]
        max_ = code_segment["max"]
        code_fmt = code_segment["msg"]
        assert isinstance(code_fmt, str)

        max_message_size = 2002
        segment_len = len(code_fmt)

        # is our msg too big for the embed?
        if segment_len > max_message_size:
            # set the block msg to None in this case
            code_fmt = None

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                reaction.emoji == self.code_highlight_emoji and user != self.bot.user and message.id == reaction.message.id
            )

        try:
            await self.bot.wait_for("reaction_add", check=check, timeout=self.highlight_timeout)

            if code_fmt is None:
                await message.channel.send("You've selected too many lines for me to display!")
                return

            msg: str = f"Showing lines `{min_}-{max_}` in: `{path}`\n{code_fmt}"
            await message.channel.send(msg, suppress_embeds=True)

        except TimeoutError:
            return


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(GitHub(bot))
