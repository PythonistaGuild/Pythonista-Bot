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

import logging
from datetime import datetime
from typing import Union

import discord
from discord import ui
from discord.ext import commands

import core


LOGGER = logging.getLogger(__name__)


def get_suggestion_type(value: str) -> str:
    options: dict[str, str] = {"1": "the guild", "2": "PythonistaBot", "3": "TwitchIO", "4": "Wavelink"}
    return options[value]


class TypeSelect(ui.Select["TypeView"]):
    def __init__(
        self,
        *,
        original_author: Union[discord.Member, discord.User],
        suggestion: str,
        webhook: discord.Webhook,
        message: discord.Message | discord.WebhookMessage | None = None,
    ):
        super().__init__()
        self.original_author = original_author
        self.suggestion = suggestion
        self.webhook = webhook
        self.message = message

        self.add_option(label="Guild", value="1", description="This suggestion applies to the guild.", emoji="\U0001f4c1")
        self.add_option(
            label="Pythonistabot", value="2", description="This suggestion applies to Pythonistabot.", emoji="\U0001f916"
        )
        self.add_option(
            label="TwitchIO",
            value="3",
            description="This suggestion applies to TwitchIO.",
            emoji="<:twitchio_illegal:1014831894417915984>",
        )
        self.add_option(
            label="Wavelink",
            value="4",
            description="This suggestion applies to Wavelink.",
            emoji="<:wavelink:753851443093438545>",
        )

    async def callback(self, interaction: discord.Interaction):
        if self.original_author != interaction.user:
            return await interaction.response.send_message(
                f"This menu is not for you. See `{core.CONFIG['prefix']}suggest` to make a suggestion!", ephemeral=True
            )
        author = self.original_author
        suggestion_type = get_suggestion_type(self.values[0])
        await interaction.response.send_message("Your suggestion has been sent!")
        embed = discord.Embed(
            title=f"Suggestion for {suggestion_type}", description=self.suggestion, timestamp=datetime.now(), color=0x7289DA
        )
        embed.set_author(name=author.name, icon_url=author.display_avatar)
        embed.set_footer(text=f"Suggestion sent by {author} (ID: {author.id})")
        await self.webhook.send(embed=embed, avatar_url=author.display_avatar, username=author.name)
        if self.message:
            await self.message.delete()


class TypeView(ui.View):
    message: discord.Message | discord.WebhookMessage

    def __init__(self, *, original_author: Union[discord.Member, discord.User], suggestion: str, webhook: discord.Webhook):
        super().__init__(timeout=180)
        self.original_author = original_author
        self.add_item(
            TypeSelect(original_author=original_author, suggestion=suggestion, webhook=webhook, message=self.message)
        )

    async def on_timeout(self):
        await self.message.delete()
        await super().on_timeout()


class Suggestions(core.Cog):
    def __init__(self, bot: core.Bot, url: str):
        self.bot = bot
        self.webhook = discord.Webhook.from_url(url, session=self.bot.session)

    @commands.group(name="suggest", brief="Send a suggestion for the server, or a library.", invoke_without_command=True)
    async def suggest(self, ctx: core.Context, *, suggestion: str | None = None):
        if not suggestion:
            return await ctx.reply("Re-execute the command. Make sure to give your suggestion this time!")
        view = TypeView(original_author=ctx.author, suggestion=suggestion, webhook=self.webhook)
        view.message = await ctx.send(
            "Please select the type of suggestion this is. Your suggestion will not be sent until this step is completed.",
            view=view,
        )


async def setup(bot: core.Bot):
    if key := core.CONFIG.get("SUGGESTIONS"):
        await bot.add_cog(Suggestions(bot, key["webhook_url"]))
    else:
        LOGGER.warning("Cannot load the SUGGESTIONS extension due to the `suggestions_webhook_url` config not existing.")
