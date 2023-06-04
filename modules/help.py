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

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import core
from constants import Channels
from core.context import Context


if TYPE_CHECKING:
    from discord.ext.commands._types import Check  # type: ignore # why does this need a stub?


FORUM_BLURB = f"""
Welcome to the help forum!
Please provide as much information as possible about your problem, and then wait for someone to help you.

A good question should include:
- your problem
- your code
- your traceback (if applicable)
- what you've tried so far

Once your issue has been solved type `{core.CONFIG['prefix']}solved` to close the thread.
""".strip()


def is_forum_thread() -> Check[Context]:
    def predicate(ctx: Context) -> bool:
        channel = ctx.channel
        if not channel.guild:
            return False

        if not isinstance(channel, discord.Thread):
            return False

        if channel.parent_id != Channels.HELP_FORUM:
            return False

        return True

    return commands.check(predicate)


class Help(commands.Cog):
    """Commands relating to the help channels/forum of Pythonista."""

    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_thread_create")
    async def forum_post_created(self, thread: discord.Thread) -> None:
        if thread.parent_id != Channels.HELP_FORUM:
            return

        channel: discord.TextChannel = thread.guild.get_channel(Channels.FORUM_LOGS)  # type: ignore
        if not channel:
            return

        await channel.send(f"{thread.owner} ({thread.owner_id}) created thread '{thread.name}' ({thread.id}).")

        await thread.send(FORUM_BLURB)

    @is_forum_thread()
    @commands.command("solved", brief="Closes a forum post", short_doc="Closes a forum post in the help channels")
    async def solved(self, ctx: core.GuildContext) -> None:
        """
        Marks a forum post as solved.
        This will archive the post, lock it, and add the solved tag.
        You must be a moderator or the post OP to solve a post.
        """
        assert isinstance(ctx.channel, discord.Thread)  # guarded by the check
        assert isinstance(ctx.channel.parent, discord.ForumChannel)  # guarded by the check

        if not ctx.author_is_mod() or ctx.author != ctx.channel.owner:
            await ctx.send("You can only mark your own posts as solved")
            return

        try:
            emoji = discord.utils.get(ctx.guild.emojis, id=578575442383208468)
            if emoji:
                await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        tag = ctx.channel.parent.get_tag(1006769269201195059)
        if not tag:
            return

        await ctx.channel.edit(
            locked=True,
            archived=True,
            applied_tags=ctx.channel.applied_tags + [tag],
            reason=f"Marked as solved by {ctx.author}",
        )

        channel = ctx.guild.get_channel(Channels.FORUM_LOGS)
        assert isinstance(channel, discord.TextChannel)  # we know the ID.

        if not channel:
            return

        msg: str = f"{ctx.author} ({ctx.author.id}) marked thread '{ctx.channel.name}' ({ctx.channel.id}) as solved."
        await channel.send(msg)


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Help(bot))
