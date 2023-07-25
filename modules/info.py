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

from typing import Union

import discord
from discord.ext import commands

import core


class InformationEmbed(discord.Embed):
    """A subclass of discord.Embed.

    This class allows to automatically get information within the class instead of recreating the embed each time

    :param author: The embed author. Expects discord.Member or discord.User
    :param entity: The Member, User, Role, TextChannel, or Guild to get information about.
    """

    def __init__(
        self,
        author: Union[discord.Member, discord.User],
        entity: Union[discord.Member, discord.User, discord.Role, discord.TextChannel, discord.Guild],
    ):
        super().__init__()
        created_at: str = f"{discord.utils.format_dt(entity.created_at)} ({discord.utils.format_dt(entity.created_at, 'R')})"
        if isinstance(entity, discord.Member) and entity.joined_at:
            joined_at = f"\n\nJoined At: {discord.utils.format_dt(entity.joined_at)} ({discord.utils.format_dt(entity.joined_at, 'R')})"
        else:
            joined_at = ""

        description: str | None = None
        start: str = f"Name: {entity.name}\n\nID: {entity.id}\n\nCreated At: {created_at}{joined_at}"
        if isinstance(entity, discord.Member):
            description = start
            self.set_thumbnail(url=entity.guild_avatar or entity.display_avatar or None)
        elif isinstance(entity, discord.User):
            description = start
            self.set_thumbnail(url=entity.display_avatar or None)
        elif isinstance(entity, discord.Role):
            description = f"{start}\n\nHoisted: {entity.hoist}\n\nMentionable: {entity.mentionable}\n\n"
        elif isinstance(entity, discord.TextChannel):
            description = f"{start}\n\nCategory: {entity.category}\n\nNSFW: {entity.nsfw}"
        else:  # Change to elif when other types are added
            description = f"{start}\n\nOwner: {entity.owner}"
            self.set_thumbnail(url=entity.icon or None)

        self.description = description
        self.set_author(name=author.name, icon_url=author.display_avatar)
        self.color = 0x7289DA


class Information(core.Cog):
    """The Mystbin file modification commands. Allows users to upload files to mystbin."""

    def __init__(self, bot: core.Bot):
        self.bot = bot

    @commands.group(
        name="information",
        brief="Get information on a user, role, or channel",
        aliases=["i", "info"],
        invoke_without_command=True,
    )
    async def info(
        self, ctx: core.Context, entity: Union[discord.Member, discord.User, discord.Role, discord.TextChannel]
    ):
        """Get information about a object
        Args:
            entity: The user, role, or TextChannel to get information about"""
        embed = InformationEmbed(ctx.author, entity)
        await ctx.send(embed=embed)

    @info.command(name="guild", brief="Get the current guild's information.")
    @commands.guild_only()
    async def guild_info(self, ctx: core.Context):
        if ctx.guild is None:
            raise commands.CheckFailure("This command must be ran in a guild.")  # Make pyright stop throwing fits
        embed = InformationEmbed(ctx.author, ctx.guild)
        await ctx.reply(embed=embed)


async def setup(bot: core.Bot):
    await bot.add_cog(Information(bot))
