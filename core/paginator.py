"""MIT License

Copyright (c) 2020 - Current PythonistaGuild

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
import asyncio
from typing import Any, Dict, List, Optional

import discord
from discord import ui  # shortcut because I'm lazy
from discord.ext.commands import CommandError, Paginator as _Paginator
from discord.utils import MISSING

__all__ = ("CannotPaginate", "Pager", "KVPager", "TextPager")


class CannotPaginate(CommandError):
    pass


class Pager(ui.View):
    message: Optional[discord.Message] = None

    def __init__(
        self,
        ctx,
        *,
        entries,
        per_page=12,
        show_entry_count=True,
        title=None,
        embed_color=discord.Color.blurple(),
        nocount=False,
        delete_after=True,
        author=None,
        author_url=None,
        stop=False,
    ):
        super().__init__()
        self.bot = ctx.bot
        self.stoppable = stop
        self.ctx = ctx
        self.delete_after = delete_after
        self.entries = entries
        self.embed_author = author, author_url
        self.channel = ctx.channel
        self.author = ctx.author
        self.nocount = nocount
        self.title = title
        self.per_page = per_page

        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1

        self.maximum_pages = pages
        self.embed = discord.Embed(colour=embed_color)
        self.paginating = len(entries) > per_page
        self.show_entry_count = show_entry_count
        self.reaction_emojis = [
            ("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}", self.first_page),
            ("\N{BLACK LEFT-POINTING TRIANGLE}", self.previous_page),
            ("\N{BLACK RIGHT-POINTING TRIANGLE}", self.next_page),
            ("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}", self.last_page),
        ]

        if stop:
            self.reaction_emojis.append(("\N{BLACK SQUARE FOR STOP}", self.stop_pages))  # type: ignore

        if ctx.guild is not None:
            self.permissions = self.channel.permissions_for(ctx.guild.me)
        else:
            self.permissions = self.channel.permissions_for(ctx.bot.user)

        if not self.permissions.embed_links:
            raise CannotPaginate("Bot does not have embed links permission.")

        if not self.permissions.send_messages:
            raise CannotPaginate("Bot cannot send messages.")

    def setup_buttons(self):
        self.clear_items()
        for emoji, button in self.reaction_emojis:
            btn = ui.Button(emoji=emoji)
            btn.callback = button  # type: ignore
            self.add_item(btn)

    def get_page(self, page: int):
        base = (page - 1) * self.per_page
        return self.entries[base : base + self.per_page]

    def get_content(self, entries: List[Any], page: int, *, first=False):
        return None

    def get_embed(self, entries: List[Any], page: int, *, first=False):
        self.prepare_embed(entries, page, first=first)
        return self.embed

    def prepare_embed(self, entries: List[Any], page: int, *, first=False):
        p = []
        for index, entry in enumerate(entries, 1 + ((page - 1) * self.per_page)):
            if self.nocount:
                p.append(entry)
            else:
                p.append(f"{index}. {entry}")

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f"Page {page}/{self.maximum_pages} ({len(self.entries)} entries)"
            else:
                text = f"Page {page}/{self.maximum_pages}"

            self.embed.set_footer(text=text)

        if self.paginating and first:
            p.append("")

        if self.embed_author[0]:
            self.embed.set_author(name=self.embed_author[0], icon_url=self.embed_author[1] or MISSING)

        self.embed.description = "\n".join(p)
        self.embed.title = self.title or MISSING

    async def show_page(self, page: int, *, first=False, msg_kwargs: Dict[str, Any] | None = None):
        self.current_page = page
        entries = self.get_page(page)
        content = self.get_content(entries, page, first=first)
        embed = self.get_embed(entries, page, first=first)

        if not self.paginating:
            return await self.channel.send(content=content, embed=embed, view=self, **msg_kwargs or {})

        if not first:
            if self.message:
                await self.message.edit(content=content, embed=embed, view=self)
            return

        self.message = await self.channel.send(content=content, embed=embed, view=self)

    async def checked_show_page(self, page: int):
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.show_page(1)

    async def last_page(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.show_page(self.maximum_pages)

    async def next_page(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self, inter: discord.Interaction):
        await inter.response.defer()
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self, inter: discord.Interaction):
        await inter.response.defer()
        if self.paginating:
            await self.show_page(self.current_page)

    async def numbered_page(self, inter: discord.Interaction):
        await inter.response.defer()
        to_delete = [await self.channel.send("What page do you want to go to?")]

        def message_check(m):
            return m.author == self.author and self.channel == m.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", check=message_check, timeout=30.0)
        except asyncio.TimeoutError:
            to_delete.append(await self.channel.send("Took too long."))
            await asyncio.sleep(5)
        else:
            page = int(msg.content)
            to_delete.append(msg)
            if page != 0 and page <= self.maximum_pages:
                await self.show_page(page)
            else:
                to_delete.append(await self.channel.send(f"Invalid page given. ({page}/{self.maximum_pages})"))
                await asyncio.sleep(5)

        try:
            await self.channel.delete_messages(to_delete)
        except Exception:
            pass

    async def stop_pages(self, interaction: discord.Interaction | None = None):
        """stops the interactive pagination session"""
        if self.delete_after and self.message:
            await self.message.delete()

        super().stop()

    stop = stop_pages  # type: ignore

    def _check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return False

        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        resp = self._check(interaction)

        if not resp:
            await interaction.response.send_message("You cannot use this menu", ephemeral=True)

        return resp

    async def paginate(self, msg_kwargs: Dict[str, Any] | None = None):
        if self.maximum_pages > 1:
            self.paginating = True

        self.setup_buttons()
        await self.show_page(1, first=True, msg_kwargs=msg_kwargs)

        await self.wait()
        if self.delete_after and self.paginating and self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass


class KVPager(Pager):
    def __init__(
        self,
        ctx,
        *,
        entries: list[tuple[str, str]],
        per_page=12,
        show_entry_count=True,
        description=None,
        title=None,
        embed_color=discord.Color.blurple(),
        **kwargs,
    ):
        super().__init__(
            ctx,
            entries=entries,
            per_page=per_page,
            show_entry_count=show_entry_count,
            title=title,
            embed_color=embed_color,
            **kwargs,
        )
        self.description = description

    def prepare_embed(self, entries: List[Any], page: int, *, first=False):
        self.embed.clear_fields()
        self.embed.description = self.description or MISSING
        self.embed.title = self.title or MISSING

        for key, value in entries:
            self.embed.add_field(name=key, value=value, inline=False)

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f"Page {page}/{self.maximum_pages} ({len(self.entries)} entries)"
            else:
                text = f"Page {page}/{self.maximum_pages}"

            self.embed.set_footer(text=text)


class TextPager(Pager):
    def __init__(self, ctx, text, *, prefix="```", suffix="```", max_size=2000, stop=False):
        paginator = _Paginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split("\n"):
            paginator.add_line(line)

        super().__init__(ctx, entries=paginator.pages, per_page=1, show_entry_count=False, stop=stop)

    def get_page(self, page):
        return self.entries[page - 1]

    def get_embed(self, entries, page, *, first=False):
        return None

    def get_content(self, entry, page, *, first=False):
        if self.maximum_pages > 1:
            return f"{entry}\nPage {page}/{self.maximum_pages}"
        return entry
