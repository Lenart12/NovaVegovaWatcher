#!/usr/bin/env python3
import asyncio
import discord
from discord.ext import commands

import watcher

bot = commands.Bot(command_prefix='prosim ', description="Lenartov robotek!")

@bot.event
async def on_ready():
    activity = discord.Game(name='Vibing on nova.vegova.si')
    await bot.change_presence(activity=activity)
    print(f'Logged in as {bot.user.name}')
    bot.add_cog(watcher.Watcher(bot))

with open('token.txt') as fh:
    token = fg.read().strip()
bot.run(token)
