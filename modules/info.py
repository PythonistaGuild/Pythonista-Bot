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

from typing import TypeVar

import discord
from discord.ext import commands

import core
from constants import GUILD_ID


EntityT = TypeVar("EntityT", discord.Member, discord.User, discord.Role, discord.abc.GuildChannel, discord.Guild)


class NoPermissions(commands.CommandError):
    pass


class Information(core.Cog):
    """Information commands which allows you to get information about users, the guild, roles, and channels."""

    def __init__(self, bot: core.Bot) -> None:
        self.bot: core.Bot = bot

    async def cog_command_error(self, ctx: core.Context, error: commands.CommandError) -> None:  # type: ignore # bad lib types.
        error = getattr(error, "original", error)

        if isinstance(error, NoPermissions):
            await ctx.send("Sorry, you don't have permissions to view details on this object.")
            return

    def _embed_factory(self, entity: EntityT) -> discord.Embed:
        embed = discord.Embed(title=f"Info on {entity.name}!", colour=discord.Colour.random())
        embed.add_field(name="ID:", value=entity.id)
        embed.timestamp = discord.utils.utcnow()

        if isinstance(entity, discord.User):
            return self._user_info(entity, embed=embed)
        elif isinstance(entity, discord.Member):
            embed = self._user_info(entity, embed=embed)  # type: ignore # superclass
            return self._member_info(entity, embed=embed)
        elif isinstance(entity, discord.Role):
            return self._role_info(entity, embed=embed)
        elif isinstance(entity, discord.abc.GuildChannel):
            return self._channel_info(entity, embed=embed)
        else:
            return self._guild_info(entity, embed=embed)

    def _member_info(self, member: discord.Member, /, *, embed: discord.Embed) -> discord.Embed:
        if member.joined_at:
            joined_at_fmt = (
                discord.utils.format_dt(member.joined_at, "F") + "\n" f"({discord.utils.format_dt(member.joined_at, 'R')})"
            )
            embed.add_field(name="Member joined the guild on:", value=joined_at_fmt)

        roles = [role.mention for role in member.roles[1:]]
        roles.reverse()
        embed.add_field(name="Member's top 5 roles:-", value="\n".join(roles[:5]), inline=False)
        embed.colour = member.colour or embed.colour

        return embed

    def _user_info(self, user: discord.User, /, *, embed: discord.Embed) -> discord.Embed:
        embed = discord.Embed(title=f"Info on {user.display_name}!", colour=discord.Colour.random())
        embed.set_author(name=user.name)
        embed.set_image(url=user.display_avatar.url)
        created_at_fmt = (
            discord.utils.format_dt(user.created_at, "F") + "\n" f"({discord.utils.format_dt(user.created_at, 'R')})"
        )
        embed.add_field(name="Account was created on:", value=created_at_fmt)

        embed.timestamp = discord.utils.utcnow()

        return embed

    def _role_info(self, role: discord.Role, /, *, embed: discord.Embed) -> discord.Embed:
        embed.colour = role.colour or embed.colour
        embed.add_field(name="Mentionable?", value=role.mentionable)
        embed.add_field(name="Hoisted?", value=role.hoist)
        embed.add_field(name="Member count:", value=len(role.members))
        embed.add_field(name="Created on:", value=discord.utils.format_dt(role.created_at, "F"))

        return embed

    def _channel_info(self, channel: discord.abc.GuildChannel, /, *, embed: discord.Embed) -> discord.Embed:
        sneaky_role = channel.guild.default_role
        permissions = channel.permissions_for(sneaky_role)

        allowed_to_read = discord.Permissions(read_messages=True, view_channel=True)

        if not permissions.is_strict_superset(allowed_to_read):
            # They cannot read this channel
            raise NoPermissions("Cannot read this channel.")

        embed.url = channel.jump_url

        embed.add_field(name="Channel type:", value=channel.type.name, inline=False)

        embed.add_field(name="Created on:", value=discord.utils.format_dt(channel.created_at, "F"), inline=False)

        is_private = not (permissions.view_channel or permissions.read_messages)
        embed.add_field(name="Private Channel?", value=is_private)

        return embed

    def _guild_info(self, guild: discord.Guild, /, *, embed: discord.Embed) -> discord.Embed:
        if guild.id != GUILD_ID:
            raise NoPermissions("Unreachable but better safe than sorry.")

        embed.add_field(name="Created on:", value=discord.utils.format_dt(guild.created_at, "F"))
        embed.set_thumbnail(url=(guild.icon and guild.icon.url))

        return embed

    @commands.group(
        name="information",
        brief="Get information on a user, role, or channel",
        aliases=["i", "info"],
        invoke_without_command=True,
    )
    async def info(
        self,
        ctx: core.Context,
        *,
        entity: discord.Member
        | discord.User
        | discord.Role
        | discord.abc.GuildChannel
        | discord.Guild = commands.CurrentGuild,
    ) -> None:
        """Get information about a specific Pythonista related object.

        entity: Accepts a Person's ID, a Role ID or a Channel ID. Defaults to showing info on the Guild.
        """
        embed = self._embed_factory(entity)  # type: ignore # we ignore because converter sadness
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: core.Bot) -> None:
    await bot.add_cog(Information(bot))
