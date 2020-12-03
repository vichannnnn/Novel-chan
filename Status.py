import discord
import random
from discord.ext import tasks, commands


class Status(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self.change_status.start()

    @tasks.loop(seconds=1800)
    async def change_status(self):

        try:

            name = ["for novel updates..", "myself developing.."]
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(name)))


        except:

            pass

    @change_status.before_loop
    async def before_status(self):
        print('Waiting...')
        await self.bot.wait_until_ready()



def setup(bot):
    bot.add_cog(Status(bot))
