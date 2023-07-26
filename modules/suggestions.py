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

from datetime import datetime
import discord
from enum import Enum
import core
from discord.ext import commands

class SuggestionEnum(Enum):
    guild = 1
    pythonistabot = 2
    twitchio = 3
    wavelink = 4


class Suggestions(core.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot

    async def cog_load(self):
        if url := core.CONFIG["Suggestions"].get("suggestions_webhook_url"):
            self.webhook = discord.Webhook.from_url(url, session=self.bot.session)

        else: # disable all commands in cog
            for command in self.walk_commands():
                command.update(enabled=False)

    @commands.group(
        name="suggest",
        brief="Send a suggestion for the server, or a library.",
        invoke_without_command=True
    )
    async def suggest(self, ctx: core.Context, suggestion_target: SuggestionEnum, *, suggestion: str):
        embed = discord.Embed(
            title=f"Suggestion for {suggestion_target.name}",
            description=suggestion,
            timestamp=datetime.now()
            )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
        await self.webhook.send(embed=embed, avatar_url=ctx.author.display_avatar, username=ctx.author.name)

async def setup(bot: core.Bot):
    await bot.add_cog(Suggestions(bot))