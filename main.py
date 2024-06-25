"""
    Chochetongo
"""
import asyncio
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="choche>", intents=intents)

#abrir el token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

#para cargar cogs
async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            
#comenzar el bot
async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)
        
asyncio.run(main())
