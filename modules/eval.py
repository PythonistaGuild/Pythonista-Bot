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

from core.bot import Bot

from core.core import Cog, Context
from utils.converters import CodeblockConverter
from utils.formatters import to_codeblock

class InvalidEval(commands.CommandError):
    """ """

class Evaluation(Cog):
    """
    Evaluation Cog. The aim of this is to provide a safe, isolated and available environment for Pythonistas to run their code.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.eval_endpoint: str = ("http://localhost:8060/eval")

    @commands.command()
    async def eval(self, ctx: Context, *, code_body: CodeblockConverter):
        """
        Evaluates your code in the form of a Discord message.

        Attributes
        ----------
        code_body: :class:`converters.CodeblockConverter` -> :class:`collections.namedtuple`
            This will attempt to convert your current passed parameter into proper Python code.
        """
        await ctx.send(code_body)
        async with self.bot.session.post(self.eval_endpoint, json={"input": code_body[1]}) as eval_response:
            if eval_response.status != 200:
                raise InvalidEval(f"{eval_response.status} - There was an issue running this eval command.") #TODO: error logging? Webhook post?
            eval_data = await eval_response.json()

        stdout = eval_data['stdout']
        return await ctx.send(to_codeblock(stdout, escape_md=False))


def setup(bot):
    """ Set's up the extension to load the Cog. """
    bot.add_cog(Evaluation(bot))