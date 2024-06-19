"""
    Chochetongo
"""
from dotenv import load_dotenv
import os
from discord_components import ComponentsBot
from music_cog import music_cog

bot = ComponentsBot(command_prefix = '!') #Para activar bot con la !
bot.add_cog(music_cog(bot= bot))

#Abrir token y aplicarlo al bot
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)