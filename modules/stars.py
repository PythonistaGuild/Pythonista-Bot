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
from typing import Optional

import asyncpg
import discord
from datetime import datetime as date
from discord.ext import commands

import core

CONFIG = core.CONFIG["STARBOARD"]
STARBOARD_CHANNEL_ID = CONFIG.get("starboard_channel_id")

STARBOARD_EMBED_COLOR = 0xFFFF00
STARBOARD_EMOJI = "⭐"
HEADER_TEMPLATE = "**{}** {} in: <#{}> ID: {}"


class JumpView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout,
        url: Optional[str],
        label_name="Jump to message",
    ):
        super().__init__(timeout=timeout)
        self.add_item(discord.ui.Button(url=url, label=label_name, style=discord.ButtonStyle.primary))


class StarboardEntry:
    exists: bool = False
    msg_id: int = 0
    channel_id: int = 0
    stars: int = 0
    bot_message_id: int = 0
    bot_content_id: int = 0

    def __init__(self, db: asyncpg.Pool, msg_id):
        self.msg_id = msg_id
        self.db = db

    async def fetch(self):
        query = """SELECT * FROM starboard_entries WHERE msg_id={}""".format(self.msg_id)

        result = await self.db.fetchrow(query)

        if result is None:
            self.exists = False
            return

        self.exists = True
        self.msg_id = result["msg_id"]
        self.channel_id = result["channel"]
        self.stars = result["stars"]
        self.bot_message_id = result["bot_message_id"]
        self.bot_content_id = result["bot_content_id"]


class Starboard(core.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot

        self.remove_on_delete: bool = CONFIG.get("remove_on_delete")
        self.entry_requirement: int = CONFIG.get("entry_requirement")
        self.starboard_channel_id: int = CONFIG.get("starboard_channel_id")
        self.pool: asyncpg.Pool = bot.pool

    def get_star(self, stars):
        if stars <= 2:
            return "✨"
        elif stars <= 4:
            return "💫"
        elif stars <= 6:
            return "⭐"
        else:
            return "🌟"

    async def add_entry(self, message_id, bot_message_id, payload_channel_id, reactions, content_id):
        entry_query = """INSERT INTO starboard_entries VALUES (
                    {},
                    {},
                    {},
                    {},
                    {}
                )""".format(
            message_id, bot_message_id, payload_channel_id, reactions, content_id
        )
        await self.pool.execute(entry_query)

    async def add_starer(self, user_id, message_id):
        starer_query = """
                INSERT INTO starers VALUES (
                    {},
                    {}
                )""".format(
            user_id, message_id
        )

        await self.pool.execute(starer_query)

    def get_formatted_time(self):
        now = date.now()
        time = now.strftime("%m/%d/%Y %I:%M %p")
        return time

    async def handle_star(self, payload):
        time = self.get_formatted_time()
        entry: StarboardEntry = StarboardEntry(self.pool, payload.message_id)
        await entry.fetch()

        if str(payload.emoji) != STARBOARD_EMOJI:
            return

        message: discord.Message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        reaction = discord.utils.get(message.reactions, emoji=STARBOARD_EMOJI)
        reaction_count = reaction.count
        if entry.exists:
            bot_msg_id = entry.bot_message_id

            query = """SELECT * FROM starers WHERE user_id={} AND msg_id={}""".format(payload.user_id, entry.msg_id)

            starer = await self.pool.fetchrow(query)

            if starer is not None:
                return

            await self.add_starer(payload.user_id, payload.message_id)

            query = """UPDATE starboard_entries SET stars = starboard_entries.stars + 1 
                                    WHERE msg_id = {}
                                """.format(
                entry.msg_id
            )

            await self.pool.execute(query)

            bot_channel = await self.bot.fetch_channel(self.starboard_channel_id)
            bot_message = await bot_channel.fetch_message(bot_msg_id)

            stars = entry.stars + 1
            star = self.get_star(stars)
            await bot_message.edit(content=HEADER_TEMPLATE.format(star, stars, payload.channel_id, payload.channel_id))
            return

        if not reaction_count >= self.entry_requirement:
            return

        star = self.get_star(reaction_count)

        embed = discord.Embed(color=STARBOARD_EMBED_COLOR)

        message_url = message.jump_url

        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar)
        embed.add_field(name="", value=message.clean_content)
        embed.set_footer(text=time)

        starboard = self.bot.get_channel(self.starboard_channel_id)

        bot_message = await starboard.send(
            HEADER_TEMPLATE.format(star, reaction_count, payload.channel_id, payload.channel_id)
        )
        content_message = await starboard.send(embed=embed, view=JumpView(url=message_url, timeout=40))

        await self.add_entry(message.id, bot_message.id, payload.channel_id, reaction.count, content_message.id)
        await self.add_starer(payload.user_id, message.id)

    async def handle_unstar(self, payload):
        entry = StarboardEntry(self.pool, payload.message_id)
        await entry.fetch()

        bot_msg_id = entry.bot_message_id
        content_id = entry.bot_content_id
        if not entry.exists:
            return

        channel = await self.bot.fetch_channel(self.starboard_channel_id)
        bot_msg = await channel.fetch_message(bot_msg_id)
        content_msg = await channel.fetch_message(content_id)

        stars = entry.stars - 1

        if stars <= 0:
            # not possible to have zero stars.
            await bot_msg.delete()
            await content_msg.delete()

            query = """DELETE FROM starboard_entries WHERE msg_id={}""".format(payload.message_id)
            await self.pool.execute(query)
            return

        star = self.get_star(stars)
        message = HEADER_TEMPLATE.format(star, stars, payload.channel_id, payload.channel_id)

        query = """DELETE FROM starers WHERE msg_id={} AND user_id={}""".format(payload.message_id, payload.user_id)
        query2 = """UPDATE starboard_entries SET stars = {} WHERE msg_id={}""".format(stars, payload.message_id)

        await self.pool.execute(query)
        await self.pool.execute(query2)
        await bot_msg.edit(content=message)

    @core.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handle_star(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.handle_unstar(payload)


async def setup(bot: core.Bot):
    await bot.add_cog(Starboard(bot))
