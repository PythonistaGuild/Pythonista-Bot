"""MIT License

Copyright (c) 2020 PythonistaGuild

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
from discord.ext import commands

import core
from core.utils import formatters

class Evaluation(core.Cog):
    """Evaluation Cog. The aim of this is to provide a safe, isolated and available environment for Pythonistas to run their code.
    """

    def __init__(self, bot: core.Bot) -> None:
        self.bot = bot
        self.eval_endpoint: str = core.CONFIG.get('SNEKBOX', 'url')

    @commands.command()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def eval(self, ctx: core.Context, *, code_body: core.CodeblockConverter) -> None:
        """Evaluates your code in the form of a Discord message.

        Parameters
        ------------
        code_body: :class:`converters.CodeblockConverter`
            This will attempt to convert your current passed parameter into proper Python code.
        """
        async with ctx.typing():

            async with self.bot.session.post(self.eval_endpoint, json={'input': code_body[1]}) as eval_response:
                if eval_response.status != 200:
                    # TODO: error logging? Error handler and webhook post. Global or local?
                    raise core.InvalidEval(eval_response.status, 'There was an issue running this eval command.')

                eval_data = await eval_response.json()


            stdout = eval_data['stdout']

            if len(stdout) > 500:
                codeblock = await self.bot.mb_client.post(stdout, syntax="py")
            else:
                codeblock = formatters.to_codeblock(stdout, escape_md=False)

            await ctx.send(f"Hey {ctx.author.display_name}, here is your eval output:\n{codeblock}")


    @eval.error
    async def eval_error_handler(self, ctx: core.Context, error: Exception) -> None:
        """Eval command error handler."""
        error = getattr(error, "original", error)

        if isinstance(error, (commands.MaxConcurrencyReached, commands.CommandOnCooldown)):
            # let's silently suppress these error, don't want to spam the reaction / message delete
            return
        elif isinstance(error, core.InvalidEval):
            await ctx.send(f"Eval failed with status code: {error.status_code}.")


def setup(bot):
    """ Set's up the extension to load the Cog. """
    bot.add_cog(Evaluation(bot))
