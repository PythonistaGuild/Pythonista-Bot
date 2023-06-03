from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

import discord
from discord.ext import commands


if TYPE_CHECKING:
    from bot import Bot

__all__ = (
    "Context",
    "GuildContext",
    "Interaction",
)

Interaction: TypeAlias = discord.Interaction["Bot"]


class Context(commands.Context["Bot"]):
    pass


class GuildContext(Context):
    guild: discord.Guild  # type: ignore # type lie due to narrowing
    author: discord.Member  # type: ignore # type lie due to narrowing
