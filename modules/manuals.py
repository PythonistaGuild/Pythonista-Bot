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

import discord
import yarl
from discord.enums import Enum
from discord.ext import commands
from discord.ext.commands.view import StringView  # type: ignore # why does this need a stub

import constants
import core
from core.utils.paginator import TextPager


class NoReturn(Exception):
    pass


class LibEnum(Enum):
    wavelink = ("https://wavelink.readthedocs.io/en/latest", constants.Colours.PYTHONISTA_BG, "wavelink")
    twitchio = ("https://twitchio.dev/en/latest/", constants.Colours.PYTHON_YELLOW, "twitchio")
    discordpy = ("https://discordpy.readthedocs.io/en/stable", 2644621, "discord.py-2")
    python = ("https://docs.python.org/3", constants.Colours.PYTHON_BLUE, None)
    aiohttp = (None, 0xFF0000, "aiohttp")


lib_names = {
    "twitchio": LibEnum.twitchio,
    "tio": LibEnum.twitchio,
    "wavelink": LibEnum.wavelink,
    "wl": LibEnum.wavelink,
    "discordpy": LibEnum.discordpy,
    "dpy": LibEnum.discordpy,
    "python": LibEnum.python,
    "py": LibEnum.python,
    "aiohttp": LibEnum.aiohttp,
}


class Manuals(commands.Cog):
    """RTFM/RTFS commands"""

    target = yarl.URL("https://idevision.net/api/public/")

    def __init__(self, bot: core.Bot, *, idevision_auth: str | None) -> None:
        self.bot = bot
        self._idevision_auth: str | None = idevision_auth

    @staticmethod
    def _cooldown_bucket(ctx: core.Context) -> commands.Cooldown | None:
        if ctx.author_is_mod():
            return None

        return commands.Cooldown(2, 5)

    def _smart_guess_lib(self, ctx: core.Context) -> LibEnum | None:
        assert ctx.channel

        if ctx.channel.id == constants.Channels.HELP_CHANNEL:
            return None  # there's not much hope here, stay quick

        if isinstance(ctx.channel, discord.Thread) and ctx.channel.parent_id == constants.Channels.HELP_FORUM:
            tags = set(x.name for x in ctx.channel.applied_tags)

            if "twitchio-help" in tags:
                return LibEnum.twitchio
            elif "wavelink-help" in tags:
                return LibEnum.wavelink
            elif "discord.py-help" in tags:
                return LibEnum.discordpy
            elif "python-help" in tags:
                return LibEnum.python

            return None

        if ctx.channel.id == constants.Channels.WAVELINK_DEV:
            return LibEnum.wavelink
        elif ctx.channel.id == constants.Channels.TWITCHIO_DEV:
            return LibEnum.twitchio

        return None

    async def get_lib(self, ctx: core.Context, query: str) -> tuple[LibEnum, str, str]:  # enum, query, notice
        if not query:
            lib = self._smart_guess_lib(ctx)

            if not lib:
                await ctx.reply("Sorry, I couldn't apply a default library to this channel. Try again with a library?")
                raise NoReturn

            await ctx.send(str(lib.value), reference=ctx.replied_message)
            raise NoReturn

        view = StringView(query)
        maybe_lib = view.get_word()
        view.skip_ws()
        final_query = view.read_rest()

        tip = ""
        lib: LibEnum | None = None

        if maybe_lib in lib_names:
            lib = lib_names[maybe_lib]
        else:
            maybe_lib = None
            final_query = query  # ignore the stringview stuff then

        if lib is None:
            lib = self._smart_guess_lib(ctx)

        if lib is None:
            await ctx.reply("Sorry, I couldn't find a library that matched. Try again with a different library?")
            raise NoReturn

        elif (
            maybe_lib
            and isinstance(ctx.channel, discord.Thread)
            and ctx.channel.parent_id == constants.Channels.HELP_FORUM
            and lib == self._smart_guess_lib(ctx)
        ):
            if 1006717008613740596 not in ctx.channel._applied_tags:  # type: ignore # other-help tag, that one doesnt get a smart guess
                tip += "\n• Tip: Forum posts with tags will automatically have the relevant libraries used, no need to specify it!"

        return lib, final_query, tip

    @commands.command(
        "rtfm",
        brief="Searches documentation",
        short_doc="Searches relevant documentation for the given input.",
        signature="[library]? [query]",
        aliases=["docs", "rtfd"],
    )
    @commands.dynamic_cooldown(_cooldown_bucket, commands.BucketType.member)  # type: ignore
    async def rtfm(self, ctx: core.Context, *, query: str) -> None:
        """
        Searches relevant documentation.
        On its own it will do its best to figure out the most relevant documentation,
        but you can always specify by prefixing the query with the library you wish to use.
        The following libraries are supported (you can use either the full name or the shorthand):

        • wavelink   | wl
        • twitchio   | tio
        • python     | py
        • discordpy  | dpy


        The following flags are available for this command:

        • --labels (Include labels in search results)
        • --clear (Clearly labels labels with a `label:` prefix. If --labels has not be set it will be implicitly set)
        """
        labels = False
        clear_labels = False

        if "--labels" in query:
            labels = True
            query = query.replace("--labels", "")

        if "--clear" in query:
            labels = clear_labels = True  # implicitly set --labels
            query = query.replace("--clear", "")

        try:
            lib, final_query, tip = await self.get_lib(ctx, query)
        except NoReturn:
            return

        if not final_query:
            await ctx.send(str(lib.value[0]) + tip, reference=ctx.replied_message)
            return

        url = self.target.with_path("/api/public/rtfm.sphinx").with_query(
            {
                "query": final_query,
                "location": str(lib.value[0]),
                "show-labels": str(labels),
                "label-labels": str(clear_labels),
            }
        )

        headers = {
            "User-Agent": f"PythonistaBot discord bot (via {ctx.author})",
        }
        if self._idevision_auth:
            headers["Authorization"] = self._idevision_auth

        async with self.bot.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await ctx.send(f"The api returned an irregular status ({resp.status}) ({await resp.text()})")
                return

            matches = await resp.json()
            if not matches["nodes"]:
                await ctx.send("Could not find anything. Sorry.")
                return

        e = discord.Embed(colour=lib.value[1])
        e.title = f"{lib.name.title()}: {final_query}"
        e.description = "\n".join(f"[`{key}`]({url})" for key, url in matches["nodes"].items())
        e.set_author(name=f"Query Time: {float(matches['query_time']):.2f}")

        await ctx.send(tip or None, embed=e)

    @commands.command(
        name="rtfs",
        brief="Searches source files",
        short_doc="Searches relevant library source for the given input.",
        signature="[library]? [query]",
        aliases=["source"],
    )
    @commands.dynamic_cooldown(_cooldown_bucket, commands.BucketType.member)  # type: ignore
    async def rtfs(self, ctx: core.Context, *, query: str) -> None:
        """
        Searches relevant library source code.
        On its own it will do its best to figure out the most relevant library,
        but you can always specify by prefixing the query with the library you wish to use.
        The following libraries are supported (you can use either the full name or the shorthand):

        • wavelink   | wl
        • twitchio   | tio
        • discordpy  | dpy
        • aiohttp    |

        The following flags are available for this command:

        • --source (Sends source code instead of links to the github repository)
        """

        source = False

        if "--source" in query:
            source = True
            query = query.replace("--source", "")

        try:
            lib, final_query, tip = await self.get_lib(ctx, query)
        except NoReturn:
            return

        if not final_query:
            await ctx.reply(str(lib.value[0]) + tip)
            return

        url = self.target.with_path("/api/public/rtfs").with_query(
            {
                "query": final_query,
                "library": str(lib.value[2]),
                "format": "links" if not source else "source",
            }
        )

        headers = {
            "User-Agent": f"PythonistaBot discord bot (via {ctx.author})",
        }
        if self._idevision_auth:
            headers["Authorization"] = self._idevision_auth

        async with self.bot.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await ctx.send(f"The api returned an irregular status ({resp.status}) ({await resp.text()})")
                return

            matches = await resp.json()
            if not matches["nodes"]:
                await ctx.send("Could not find anything. Sorry.")
                return

        nodes: dict[str, str] = matches["nodes"]

        if not source:
            out = [f"[{name}]({url})" for name, url in nodes.items()]

            author: str = f"query Time: {float(matches['query_time']):.03f} • commit {matches['commit'][:6]}"
            footer: str | None = tip or None

            embed: discord.Embed = discord.Embed(title=f"{lib.name.title()}: {final_query}", colour=lib.value[1])
            embed.description = "\n".join(out)
            embed.set_author(name=author)
            embed.set_footer(text=footer)

            await ctx.send(embed=embed)

        else:
            n = next(iter(nodes.items()))
            await ctx.send(
                f"Showing source for `{n[0]}`\nCommit: {matches['commit'][:6]}" + tip, reference=ctx.replied_message
            )

            pages = TextPager(ctx, n[1], prefix="```py", reply_author_takes_paginator=True)
            await pages.paginate()


async def setup(bot: core.Bot) -> None:
    idevision_auth_key = core.CONFIG["TOKENS"].get("idevision")
    await bot.add_cog(Manuals(bot, idevision_auth=idevision_auth_key))
