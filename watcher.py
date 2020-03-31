import asyncio
from discord.ext import commands, tasks

import aioconsole
import traceback
import pagelib

import json

class Watcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.school_url = 'https://nova.vegova.si/'
        self.watcher.start()

        with open('watcher_items.json', 'r') as fh:
            self.bot.watcher_items = json.load(fh)

        print(f'Started watcher\nItems={len(self.bot.watcher_items)}')

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def vklopi(self, ctx, razred: str):
        await aioconsole.aprint(f'{ctx.author.name}: {ctx.message.content}')
        if not (len(razred) == 5 and \
            razred[0] in 'egr' and \
            razred[1] == '-' and \
            razred[2] in '1234' and \
            razred[3] == '-' and \
            razred[4] in 'abcd'):
            await ctx.channel.send('Razred ne ustreza formatu `s-l-o`, s=[e,g,r] l=[1,2,3,4] o=[a,b,c,d] (npr. `r-4-b`) ')
            return
        else:
            url = f'{self.bot.school_url}{razred}'
            tasks = pagelib.split_page(pagelib.get_page(url))

            if len(tasks) == 0:
                await ctx.channel.send(f'Program ne najde nic navodil za `{url}`')
                return
            else:
                r = self.bot.watcher_items.get(razred, None)
                
                if r:
                    channels = r.get('channels', None)
                    if channels:
                        if ctx.channel.id not in channels:
                            self.bot.watcher_items[razred]['channels'].append(ctx.channel.id)
                        else:
                            await ctx.channel.send(f'Sporocanje za `{url}` v <#{ctx.channel.id}> ze vklopljeno')
                            return
                    else:
                        self.bot.watcher_items[razred] = {
                            "channels" : [ctx.channel.id],
                            "old_tasks" : tasks
                        }
                else:
                    self.bot.watcher_items[razred] = {
                        "channels" : [ctx.channel.id],
                        "old_tasks" : tasks
                    }

                with open('watcher_items.json', 'w') as fh:
                    json.dump(self.bot.watcher_items, fh)
                
                await ctx.channel.send(f'Vklopljeno sporocanje za `{url}` v <#{ctx.channel.id}>')

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def izklopi(self, ctx, razred: str):
        if ctx.channel.id in self.bot.watcher_items[razred]['channels']:
            self.bot.watcher_items[razred]['channels'].remove(ctx.channel.id)

        await ctx.channel.send(f'Izklopjeno sporocanje za { razred } v <#{ctx.channel.id}>')

        with open('watcher_items.json', 'w') as fh:
            json.dump(self.bot.watcher_items, fh)

    @tasks.loop(minutes=5.0)
    async def watcher(self):
        try:
            save = False
            for razred, data in self.bot.watcher_items.items():
                if len(data['channels']) == 0:
                    continue

                url = f'{self.bot.school_url}{razred}'
                html = pagelib.get_page(url)
                tasks = pagelib.split_page(html)
                old_tasks = data['old_tasks']
                diff = pagelib.get_diff(old_tasks, tasks)

                out = ''
                for ime, nal in diff.items():
                    if nal:
                        out += f'**{ime}**\n```{nal}```\n'

                if out:
                    self.bot.watcher_items[razred]['old_tasks'] = tasks
                    save = True

                    await aioconsole.aprint(f'Novi diff za {razred}:\n{out}')
                    out = f'**OBVESTILO ZA {razred}**\n' + out

                    for channel_id in data['channels']:
                        channel = self.bot.get_channel(channel_id)
                        await aioconsole.aprint(f'Sending to {channel_id}')
                        await channel.send(out)

            if save:
                with open('watcher_items.json', 'w') as fh:
                    json.dump(self.bot.watcher_items, fh)

        except Exception:
            await aioconsole.aprint(f'Exception\n==========\n{ traceback.format_exc() }\n==========')