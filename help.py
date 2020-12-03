import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect('prefix.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row


class Help(commands.Cog, name="Help"):

    def __init__(self, bot):
        self.bot = bot
        print("help.py extension has loaded!")

    commands.command(
        name='help',
        description='The help command!',
        aliases=['commands', 'command'],
        usage='cog'
    )

    @commands.command()
    async def help(self, ctx):

        reactions = ['📖']
        reactionsCogs = ['📖 BoxNovel Notifications']

        cogs = [cog for cog in self.bot.cogs.keys()]

        prefixDictionary = {}

        for prefix in c.execute(f'SELECT guild_id, prefix FROM prefix'):
            prefixDictionary.update({prefix[0]: f"{prefix[1]}"})

        currentPrefix = prefixDictionary[ctx.message.guild.id]

        embed = discord.Embed(title="Novel-chan Help Menu",
                              description=f"`{currentPrefix}myprefix` for this server's prefix and `{currentPrefix}setprefix` to change this server's prefix.")
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(
            text=f"Requested by {ctx.message.author.name} :: {ctx.message.guild}'s prefix currently is {currentPrefix}",
            icon_url=self.bot.user.avatar_url)

        hidden_cogs = ['Help', 'Functions', 'Status']

        for cog in cogs:

            if cog not in hidden_cogs:

                try:

                    cog_commands = self.bot.get_cog(cog).get_commands()
                    commands_list = ''

                    for comm in cog_commands:
                        commands_list += f'`{comm}` '

                    embed.add_field(name=cog, value=commands_list, inline=True)

                except:

                    pass

        msg = await ctx.send(embed=embed)

        for react in reactions:

            await msg.add_reaction(react)

        def check(reaction, user):

            return str(reaction.emoji) in reactions and user == ctx.message.author and reaction.message.id == msg.id

        async def handle_reaction(reaction, msg, check):

            await msg.remove_reaction(reaction, ctx.message.author)

            if str(reaction.emoji) == '📖':

                help_embed = discord.Embed(title=f'{reactionsCogs[0]} Help')
                help_embed.set_footer(
                        text=f"Requested by {ctx.message.author.name} :: {ctx.message.guild}'s prefix currently is {currentPrefix}",
                        icon_url=self.bot.user.avatar_url)

                cog_commands = self.bot.get_cog(f"{reactionsCogs[0]}").get_commands()
                commands_list = ''

                for comm in cog_commands:
                    commands_list += f'**{comm.name}** - {comm.description}\n'

                    help_embed.add_field(name=comm, value=comm.description, inline=True)

                await msg.edit(embed=help_embed)

            else:

                return

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            await handle_reaction(reaction, msg, check)

        reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
        await handle_reaction(reaction, msg, check)






def setup(bot):
    bot.add_cog(Help(bot))
