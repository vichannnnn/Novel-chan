import discord
import math
from discord.ext import commands
from discord.ext.commands import has_permissions
import sqlite3
from authentication import bot_token
from datetime import datetime
import pytz
import traceback

now = int(datetime.now(pytz.timezone("Singapore")).timestamp())

conn = sqlite3.connect('prefix.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

startup_extensions = ['functions', 'Status', 'webScraper']
help_extensions = ['help']

c.execute('''CREATE TABLE IF NOT EXISTS prefix (
        `guild_id` INT PRIMARY KEY,
        `prefix` TEXT)''')


async def determine_prefix(bot, message):

    prefixDictionary = {}

    for prefix in c.execute(f'SELECT guild_id, prefix FROM prefix'):
        prefixDictionary.update({prefix[0]: f"{prefix[1]}"})

    currentPrefix = prefixDictionary[message.guild.id]

    return commands.when_mentioned_or(currentPrefix)(bot, message)


bot = commands.Bot(command_prefix=determine_prefix, help_command=None)

if __name__ == "__main__":

    for extension in startup_extensions:

        try:

            bot.load_extension(extension)
            print(f'{extension}.py successfully loaded!')

        except Exception as e:

            exc = f'{type(e).__name__}: {e}'
            print(f'Failed to load extension {extension}\n{exc}')
            traceback.print_exc()


@bot.command(help="Loads an extension. Bot Owner only!")
@commands.is_owner()
async def load(ctx, extension_name: str):
    try:

        bot.load_extension(extension_name)

    except (AttributeError, ImportError) as e:

        await ctx.send(f"```py\n{type(e).__name__}: {str(e)}\n```")
        return

    await ctx.send(f"{extension_name} loaded.")


@bot.command(help="Unloads an extension. Bot Owner only!")
@commands.is_owner()
async def unload(ctx, extension_name: str):
    bot.unload_extension(extension_name)
    await ctx.send(f"{extension_name} unloaded.")


@bot.command()
@has_permissions(manage_messages=True)
async def setprefix(ctx, new):
    guild = ctx.message.guild.id
    name = bot.get_guild(guild)

    for key, value in c.execute('SELECT guild_id, prefix FROM prefix'):

        if key == guild:
            c.execute(''' UPDATE prefix SET prefix = ? WHERE guild_id = ? ''', (new, guild))
            conn.commit()
            embed = discord.Embed(description=f"{name}'s Prefix has now changed to `{new}`.")
            await ctx.send(embed=embed)


@bot.command()
async def myprefix(ctx):
    c.execute(f'SELECT prefix FROM prefix WHERE guild_id = {ctx.message.guild.id}')
    currentPrefix = c.fetchall()[0][0]

    name = bot.get_guild(ctx.message.guild.id)
    embed = discord.Embed(description=f"{name}'s Prefix currently is `{currentPrefix}`.")
    await ctx.send(embed=embed)



@bot.event
async def on_ready():
    print(f"Logging in as {str(bot.user)}")
    print(f"{str(bot.user)} has connected to Discord!")
    print(f"Current Discord Version: {discord.__version__}")
    print(f"Number of servers currently connected to {str(bot.user)}:")
    print(len([s for s in bot.guilds]))
    print("Number of players currently connected to Bot:")
    print(sum(guild.member_count for guild in bot.guilds))

    guild_id_database = []

    for row in c.execute('SELECT guild_id FROM prefix'):
        guild_id_database.append(row[0])

    async for guild in bot.fetch_guilds():

        if guild.id not in guild_id_database:
            c.execute(''' INSERT OR REPLACE INTO prefix VALUES (?, ?)''', (guild.id, '//'))
            conn.commit()
            print(f"Bot started up: Created a prefix database for {guild.id}: {guild}")


@bot.event
async def on_guild_join(guild):
    guild_id_database = []

    for row in c.execute('SELECT guild_id FROM prefix'):
        guild_id_database.append(row[0])

    if guild.id not in guild_id_database:
        c.execute(''' INSERT OR REPLACE INTO prefix VALUES (?, ?)''', (guild.id, '//'))
        conn.commit()
        print(f"Bot joined a new server: Created a prefix database for {guild.id}: {guild}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):

        seconds = error.retry_after
        minutes = seconds / 60
        hours = seconds / 3600

        if ctx.message.author.id == 624251187277070357:
            await ctx.reinvoke()
            return

        if seconds / 60 < 1:

            embed = discord.Embed(
                description=f'You\'re using this command too often! Try again in {str(int(seconds))} seconds!')
            await ctx.send(embed=embed)

        elif minutes / 60 < 1:

            embed = discord.Embed(
                description=f'You\'re using this command too often! Try again in {math.floor(minutes)} minutes and {(int(seconds) - math.floor(minutes) * 60)} seconds!')
            await ctx.send(embed=embed)

        else:

            embed = discord.Embed(
                description=f'You\'re using this command too often! Try again in {math.floor(hours)} hours, {(int(minutes) - math.floor(hours) * 60)} minutes, {(int(seconds) - math.floor(minutes) * 60)} seconds!')
            await ctx.send(embed=embed)

    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(description='You do not have the permission to do this!')
        await ctx.send(embed=embed)

    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description='Missing arguments on your command! Please check and retry again!')
        await ctx.send(embed=embed)
    raise error


@bot.command()
async def ping(ctx):
    embed = discord.Embed(description=f"Pong! This took {bot.latency} seconds!")
    await ctx.send(embed=embed)


bot.remove_command('help')

if __name__ == "__main__":
    for extension in help_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
            print(f'Failed to load extension {extension}\n{exc}')

bot.run(f'{bot_token}', reconnect=True)
