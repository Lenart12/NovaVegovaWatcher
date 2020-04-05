import asyncio
import discord
from discord.ext import commands, tasks

import aioconsole
import traceback
import pagelib

import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format_channel(channel: discord.TextChannel):
    if channel:
        return f'{channel.guild.name} > #{channel.name} ({channel.id})'
    else:
        return 'None > #None (None)'

class Watcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.school_url = 'https://nova.vegova.si/'
        self.watcher.start()

        with open('watcher_items.json', 'r') as fh:
            self.bot.watcher_items = json.load(fh)

        print(f'{bcolors.HEADER}Monitoring:{bcolors.ENDC}')
        if self.bot.watcher_items:
            for razred, data in self.bot.watcher_items.items():
                print(f'{bcolors.HEADER}"{razred}"{bcolors.ENDC} : {bcolors.OKGREEN}[{", ".join(format_channel(self.bot.get_channel(c)) for c in data["channels"])}]{bcolors.ENDC}')

    def cog_unload(self):
        self.watcher.cancel()

    @commands.is_owner()
    @commands.command(name="update_old_tasks")
    async def update_old_tasks(self, ctx):
        for razred, _ in self.bot.watcher_items.items():
            url = f'{self.bot.school_url}{razred}'
            tasks = pagelib.split_page(pagelib.get_page(url))
            self.bot.watcher_items[razred]['old_tasks'] = tasks

        with open('watcher_items.json', 'w') as fh:
            json.dump(self.bot.watcher_items, fh)

        await aioconsole.aprint(f'{bcolors.OKGREEN}Force updated tasks{bcolors.ENDC}')

    @commands.is_owner()
    @commands.command(name="tell_all")
    async def tell_all(self, ctx, *, msg: str):
        await aioconsole.aprint(f'{bcolors.OKBLUE}Sending {msg} to all channels{bcolors.ENDC}')
        for razred, data in self.bot.watcher_items.items():
            await aioconsole.aprint(f'{bcolors.HEADER}{razred}:{bcolors.ENDC}')
            for channel_id in data['channels']:
                try:
                    channel = self.bot.get_channel(channel_id)
                    await channel.send(msg)
                    await aioconsole.aprint(f'{bcolors.OKBLUE}Sending to {format_channel(channel)}{bcolors.ENDC}')
                except Exception as e:
                    await aioconsole.aprint(f'{bcolors.WARNING}Couldn\'t send to {format_channel(channel)} - {e}{bcolors.ENDC}')


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith('prosim '):
            await aioconsole.aprint(f'{bcolors.HEADER}{format_channel(message.channel)} {bcolors.OKBLUE}{message.author.name}{bcolors.ENDC}: {message.content}')

    @commands.Cog.listener()
    async def on_error(self, error, *args, **kwargs):
        await aioconsole.aprint(f'{bcolors.FAIL}Exception\n==========\n{ traceback.format_exc() }\n=========={bcolors.ENDC}')
        await aioconsole.aprint(f'Error: {error}\nArgs: {args}\nKwargs: {kwargs}{bcolors.ENDC}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.CommandNotFound):
            err = f'Ta ukaz ne obstaja'
            await aioconsole.aprint(f'{bcolors.OKBLUE}Command not found{bcolors.ENDC}')
        elif isinstance(error, commands.MissingPermissions):
            err = f'Nimas pravic za ta ukaz (administrator)'
            await aioconsole.aprint(f'{bcolors.OKBLUE}Missing permissions{bcolors.ENDC}')
        elif isinstance(error, commands.MissingRequiredArgument):
            err = f'Premalo argumentov - `prosim help [ukaz]`'
            await aioconsole.aprint(f'{bcolors.OKBLUE}Missing required argument{bcolors.ENDC}')
        elif isinstance(error, commands.BadArgument):
            err = f'Napacni argument/i - `prosim help [ukaz]`'
            await aioconsole.aprint(f'{bcolors.OKBLUE}Bad argument{bcolors.ENDC}')
        else:
            err = f'Napaka - {error}'
            await aioconsole.aprint(f'{bcolors.OKBLUE}Command error: {error}{bcolors.ENDC}')

        try:
            await ctx.channel.send(err)
        except discord.Forbidden:
            await ctx.message.author.send(f'Nimam pravice posiljati sporocil v {format_channel(ctx.channel)}\n{err}')
            await aioconsole.aprint(f'{bcolors.WARNING}Cant send to {format_channel(ctx.channel)}! Forbidden{bcolors.ENDC}')



    @commands.command(name='watching')
    @commands.is_owner()
    async def dump_watching(self, ctx):
        out = '```json\n'
        out_obj = {}
        for razred, data in self.bot.watcher_items.items():
            out_obj[razred] = [format_channel(self.bot.get_channel(c)) for c in data['channels']]
        out += json.dumps(out_obj, sort_keys=True, indent=4)
        out += '```'
        try:
            await ctx.channel.send(out)
            await aioconsole.aprint(f'{bcolors.OKBLUE}Dumped watching command into {format_channel(ctx.channel)}{bcolors.ENDC}')
        except discord.Forbidden:
            await aioconsole.aprint(f'{bcolors.WARNING}Cant send to {format_channel(ctx.channel)}! Forbidden{bcolors.ENDC}')

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def vklopi(self, ctx, razred: str):
        if not (len(razred) == 5 and \
            razred[0] in 'egr' and \
            razred[1] == '-' and \
            razred[2] in '1234' and \
            razred[3] == '-' and \
            razred[4] in 'abcd'):
            await ctx.channel.send('Razred ne ustreza formatu `s-l-o`, s=[e,g,r] l=[1,2,3,4] o=[a,b,c,d] (npr. `r-4-b`) ')
            await aioconsole.aprint(f'{bcolors.OKBLUE}Not turing on - Invalid format{bcolors.ENDC}')
            return
        else:
            url = f'{self.bot.school_url}{razred}'
            tasks = pagelib.split_page(pagelib.get_page(url))

            if len(tasks) == 0:
                await ctx.channel.send(f'Program ne najde nic navodil za `{url}`')
                await aioconsole.aprint(f'{bcolors.FAIL}Not turing on - no tasks for {razred}{bcolors.ENDC}')
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
                            await aioconsole.aprint(f'{bcolors.OKBLUE}Already turned on for {razred} - {format_channel(ctx.channel)}{bcolors.ENDC}')
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
                
                try:
                    await ctx.channel.send(f'Vklopljeno sporocanje za `{url}` v <#{ctx.channel.id}>')
                    await aioconsole.aprint(f'{bcolors.OKGREEN}Added {format_channel(ctx.channel)} to new {razred}{bcolors.ENDC}')
                except discord.Forbidden:
                    await ctx.message.author.send(f'Nimam pravice posiljanja sporocil v {format_channel(ctx.channel)}')
                    await aioconsole.aprint(f'{bcolors.OKBLUE}Not turing on - forbidden on {format_channel(ctx.channel)}{bcolors.ENDC}')

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def izklopi(self, ctx, razred: str):
        if ctx.channel.id in self.bot.watcher_items[razred]['channels']:
            self.bot.watcher_items[razred]['channels'].remove(ctx.channel.id)

        with open('watcher_items.json', 'w') as fh:
            json.dump(self.bot.watcher_items, fh)

        await aioconsole.aprint(f'{bcolors.OKBLUE}Turned off {razred} for {format_channel(ctx.channel)}{bcolors.ENDC}')
        await ctx.channel.send(f'Izklopjeno sporocanje za { razred } v <#{ctx.channel.id}>')


    @tasks.loop(minutes=15.0)
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
                        out += f'**{ime}**\n```diff\n{nal}```\n'

                if out:
                    self.bot.watcher_items[razred]['old_tasks'] = tasks
                    save = True

                    await aioconsole.aprint(f'{bcolors.HEADER}Novi diff za {razred}:{bcolors.ENDC}\n{out}')
                    out = f'**OBVESTILO ZA {razred}**\n' + out

                    for channel_id in data['channels']:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            try:
                                await channel.send(out)
                                await aioconsole.aprint(f'{bcolors.OKGREEN}Sending to {format_channel(channel)}{bcolors.ENDC}')
                            except discord.Forbidden:
                                await aioconsole.aprint(f'{bcolors.WARNING}Cant send to {format_channel(channel)}! Forbidden{bcolors.ENDC}')

                        else:
                            await aioconsole.aprint(f'{bcolors.WARNING}Cant send to {channel_id}! - no channel{bcolors.ENDC}')


            if save:
                with open('watcher_items.json', 'w') as fh:
                    json.dump(self.bot.watcher_items, fh)

        except Exception:
            await aioconsole.aprint(f'{bcolors.FAIL}Exception\n==========\n{ traceback.format_exc() }\n=========={bcolors.ENDC}')