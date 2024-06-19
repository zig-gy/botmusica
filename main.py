"""
    Chochetongo
"""

from discord_components import ComponentsBot
from music_cog import music_cog

bot = ComponentsBot(command_prefix = '!') #Para activar bot con la !
bot.add_cog(music_cog(bot= bot))

#Abrir token.txt y leer el token del bot y conectarlo al bot
with open('token.txt', 'r') as file:
    token = file.readlines()[0]
    print(token)
bot.run(token)