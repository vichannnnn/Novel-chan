import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
import sqlite3
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
import re
import functions
import traceback
import aiohttp
import asyncio

conn = sqlite3.connect('bot.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row


class webScraper(commands.Cog, name="📖 BoxNovel Notifications"):
    def __init__(self, bot):
        self.bot = bot
        self.scrapingHandler.start()

    @commands.command(description="`//embedsettings [colour code e.g. 0xffff0]`\n\nSets the embed colour for Novel-chan.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def embedsettings(self, ctx, colour):

        try:
            c.execute(f''' UPDATE SERVER SET embed = ? WHERE server_id = ? ''', (colour, ctx.message.guild.id))
            conn.commit()
            await functions.requestEmbedTemplate(ctx,
                                                 f"☑️ Embed colour successfully set to `{colour}` for `{ctx.message.guild}`.",
                                                 ctx.message.author)
        except ValueError:

            traceback.print_exc()

    @commands.command(
        description="`//uchannel [channel mention]`\n\nAdds an novel update notification channel for the server.")
    @has_permissions(administrator=True)
    async def uchannel(self, ctx, channel: discord.TextChannel):

        c.execute('''UPDATE server SET updateChannel = ? WHERE server_id = ? ''', (channel.id, ctx.guild.id))
        conn.commit()

        await functions.requestEmbedTemplate(ctx,
                                             f"☑ Novel updates notification successfully set to {channel.mention}.",
                                             ctx.message.author)

    @commands.command(description="`//updater [link]`\n\nRemoves a novel from BoxNovel that is currently receiving notifications on.")
    @has_permissions(administrator=True)
    async def updater(self, ctx, inputLink):

        if not re.findall(r'(https?://[^\s]+)', inputLink):
            await functions.requestEmbedTemplate(ctx, f"❌ Invalid URL provided!", ctx.message.author)
            return

        linkDatabase = []

        for link in c.execute('''SELECT url FROM scraping'''):
            linkDatabase.append(link[0])

        if inputLink not in linkDatabase:
            await functions.requestEmbedTemplate(ctx, f"❌ Novel is currently not being watched!", ctx.message.author)
            return

        c.execute('''DELETE FROM scraping where url = ?''', (inputLink,))
        conn.commit()

        c.execute('''DELETE FROM website where url = ?''', (inputLink,))
        conn.commit()

        page = urlopen(inputLink)

        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        parsed_html = BeautifulSoup(html, features="lxml")

        title = parsed_html.find('title')
        title2 = title.string
        updatedTitle = title2.replace(' – BoxNovel', '')

        await functions.requestEmbedTemplate(ctx,
                                             f"☑ **{updatedTitle}** notification successfully stopped.",
                                             ctx.message.author)

    @commands.command(description="`//check`\n\nDoes an immediate check for new novel updates.")
    async def check(self, ctx):

        embed = discord.Embed(description="Now checking for novel updates..", colour=functions.embedColour(ctx.message.guild.id))
        msg = await ctx.send(embed=embed)

        listOfLinks = [links[0] for links in c.execute(''' SELECT url FROM scraping ''')]

        for URLs in listOfLinks:

            URLtoBeScraped = URLs

            async def fetch(session, url):
                async with session.get(url) as response:
                    return await response.text()

            async def main():
                async with aiohttp.ClientSession() as session:

                    html = await fetch(session, URLtoBeScraped)
                    parsed_html = BeautifulSoup(html, features="lxml")

                    title = parsed_html.find('title')
                    title2 = title.string
                    updatedTitle = title2.replace(' – BoxNovel', '')

                    productDivs = parsed_html.body.findAll('li', attrs={'class': 'wp-manga-chapter'})

                    chapterDatabase = [div[0] for div in
                                       c.execute(f'''SELECT releasedChapters FROM website WHERE url = ? ''',
                                                 (URLtoBeScraped,))]

                    i = 0

                    for div in productDivs:

                        divLink = div.find('a')['href']

                        if divLink not in chapterDatabase:

                            i += 1

                            newText = div.text.strip()
                            newText2 = newText.rsplit(' ', 3)[0]

                            c.execute('''INSERT OR REPLACE INTO website VALUES (?, ?)''',
                                      (URLtoBeScraped, div.find('a')['href']))
                            conn.commit()

                            print(f"{newText2}")
                            print(
                                f"**{updatedTitle}** has just released a new chapter!\n\nLink: {div.find('a')['href']}")
                            print(f"Released: {div.find('i').text}")

                            c.execute('''SELECT updateChannel FROM server''')
                            allChannels = c.fetchall()

                            for channels in allChannels:

                                channelsObject = self.bot.get_channel(channels[0])
                                embed = discord.Embed(title=f"{newText2}",
                                                      description=f"**{updatedTitle}** has just released a new chapter!\n\nLink: {div.find('a')['href']}",
                                                      timestamp=datetime.utcnow(),
                                                      colour=functions.embedColour(channelsObject.guild.id))
                                embed.set_footer(text=f"Released: {div.find('i').text}",
                                                 icon_url="https://i.imgur.com/fTIyhZp.gif")

                                await channelsObject.send(embed=embed)

                                if channelsObject.guild.id == 624254314130440203:
                                    await channelsObject.send("<@624251187277070357>")

                embed = discord.Embed(description=f"Finished checking for **{updatedTitle}**. {i} new chapters found.\n\nIn process of checking for novel updates..", colour=functions.embedColour(ctx.message.guild.id))
                await msg.edit(embed=embed)

                print(f"Checked {updatedTitle}!")



            await main()





        embed = discord.Embed(description="Finished checking for novel updates!", colour=functions.embedColour(ctx.message.guild.id))
        await msg.edit(embed=embed)



    @commands.command(description="`//update [link]`\n\nAdds a novel from BoxNovel to be notified on for new chapters.")
    @has_permissions(administrator=True)
    async def update(self, ctx, link):

        if not re.findall(r'(https?://[^\s]+)', link):
            await functions.requestEmbedTemplate(ctx, f"❌ Invalid URL provided!", ctx.message.author)
            return

        c.execute('''INSERT OR REPLACE INTO scraping VALUES (?) ''', (link,))
        conn.commit()

        page = urlopen(link)

        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        parsed_html = BeautifulSoup(html, features="lxml")

        title = parsed_html.find('title')
        title2 = title.string
        updatedTitle = title2.replace(' – BoxNovel', '')

        productDivs = parsed_html.body.findAll('li', attrs={'class': 'wp-manga-chapter'})

        for div in productDivs[:3]:

            newText = div.text.strip()
            newText2 = newText.rsplit(' ', 3)[0]

            embed = discord.Embed(title=f"{newText2}",
                                  description=f"**{updatedTitle}** has just released a new chapter!\n\nLink: {div.find('a')['href']}",
                                  timestamp=datetime.utcnow(),
                                  colour=functions.embedColour(ctx.guild.id))

            embed.set_footer(text=f"Released: {div.find('i').text}", icon_url="https://i.imgur.com/fTIyhZp.gif")

            c.execute('''SELECT updateChannel FROM server''')
            allChannels = c.fetchall()

            for channels in allChannels:
                channelsObject = self.bot.get_channel(channels[0])
                await channelsObject.send(embed=embed)

        for div in productDivs:
            c.execute('''INSERT OR REPLACE INTO website VALUES (?, ?)''', (link, div.find('a')['href']))
            conn.commit()

        await functions.requestEmbedTemplate(ctx,
                                             f"☑ **{updatedTitle}** is now being monitored for chapter release updates!",
                                             ctx.message.author)

    @tasks.loop(seconds=600.0)
    async def scrapingHandler(self):

        try:

            listOfLinks = [links[0] for links in c.execute(''' SELECT url FROM scraping ''')]

            for URLs in listOfLinks:

                URLtoBeScraped = URLs

                async def fetch(session, url):
                    async with session.get(url) as response:
                        return await response.text()

                async def main():
                    async with aiohttp.ClientSession() as session:

                        html = await fetch(session, URLtoBeScraped)
                        parsed_html = BeautifulSoup(html, features="lxml")

                        title = parsed_html.find('title')
                        title2 = title.string
                        updatedTitle = title2.replace(' – BoxNovel', '')

                        productDivs = parsed_html.body.findAll('li', attrs={'class': 'wp-manga-chapter'})

                        chapterDatabase = [div[0] for div in
                                           c.execute(f'''SELECT releasedChapters FROM website WHERE url = ? ''',
                                                     (URLtoBeScraped,))]

                        for div in productDivs:

                            divLink = div.find('a')['href']

                            if divLink not in chapterDatabase:
                                newText = div.text.strip()
                                newText2 = newText.rsplit(' ', 3)[0]

                                c.execute('''INSERT OR REPLACE INTO website VALUES (?, ?)''',
                                          (URLtoBeScraped, div.find('a')['href']))
                                conn.commit()

                                print(f"{newText2}")
                                print(
                                    f"**{updatedTitle}** has just released a new chapter!\n\nLink: {div.find('a')['href']}")
                                print(f"Released: {div.find('i').text}")

                                c.execute('''SELECT updateChannel FROM server''')
                                allChannels = c.fetchall()

                                for channels in allChannels:

                                    channelsObject = self.bot.get_channel(channels[0])
                                    embed = discord.Embed(title=f"{newText2}",
                                                          description=f"**{updatedTitle}** has just released a new chapter!\n\nLink: {div.find('a')['href']}",
                                                          timestamp=datetime.utcnow(),
                                                          colour=functions.embedColour(channelsObject.guild.id))
                                    embed.set_footer(text=f"Released: {div.find('i').text}",
                                                     icon_url="https://i.imgur.com/fTIyhZp.gif")

                                    await channelsObject.send(embed=embed)

                                    if channelsObject.guild.id == 624254314130440203:
                                        await channelsObject.send("<@624251187277070357>")

                        print(f"Checked {updatedTitle}!")



                await main()


        except Exception as e:

            traceback.print_exc()


    @scrapingHandler.before_loop
    async def before_status(self):
        print('Waiting to scrape websites...')
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(webScraper(bot))
