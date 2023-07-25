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
from discord.ext import commands
import core, typing
#from typing import TYPE_CHECKING, Any

class InformationEmbed(discord.Embed):
    def __init__(self, author: typing.Union[discord.Member, discord.User], entity: typing.Union[discord.Member, discord.User, discord.Role, discord.TextChannel, discord.Guild]):
        created_at: str = f"{discord.utils.format_dt(entity.created_at)} ({discord.utils.format_dt(entity.created_at, 'R')})"
        if isinstance(entity, discord.Member) and entity.joined_at:
            joined_at = f"\nJoined At: {discord.utils.format_dt(entity.joined_at)} ({discord.utils.format_dt(entity.joined_at, 'R')})"
        else:
            joined_at = None


        description: str | None = None
        start: str = f"Name: {entity.name}\nID: {entity.id}\nCreated At: {created_at}{joined_at}"
        if isinstance(entity, discord.Member):
            description = start
        elif isinstance(entity, discord.User):
            description = start
        elif isinstance(entity, discord.Role):
            description = f"{start}\nHoisted: {entity.hoist}\nMentionable: {entity.mentionable}\n"
        elif isinstance(entity, discord.TextChannel):
            description = f"{start}\nCategory: {entity.category}\nNSFW: {entity.nsfw}"
        else: # Change to elif when other types are added
            description = f"{start}\nOwner: {entity.owner}"

        self.description = description
        self.set_author(name=author.name, icon_url=author.display_avatar)
        self.color = 0x7289da


class Information(core.Cog):
    """The Mystbin file modification commands. Allows users to upload files to mystbin."""
    def __init__(self, bot: core.Bot):
        self.bot = bot

    @commands.group(
        name="information",
        brief="Get information on a user, role, or channel",
        aliases=['i', 'info'],
        invoke_without_command=True
    )
    async def info(self, ctx: core.Context, entity: typing.Union[discord.Member, discord.User, discord.Role, discord.TextChannel]):
        embed = InformationEmbed(ctx.author, entity)
        await ctx.send(embed=embed)

    @info.command(
        name="guild",
        brief="Get the current guild's information."
                )
    @commands.guild_only()
    async def guild_info(self, ctx: core.Context):
        if ctx.guild == None:
            raise commands.CheckFailure("This command must be ran in a guild.") # Make pyright stop throwing fits
        embed = InformationEmbed(ctx.author, ctx.guild)
        await ctx.reply(embed=embed)

async def setup(bot: core.Bot):
    await bot.add_cog(Information(bot))