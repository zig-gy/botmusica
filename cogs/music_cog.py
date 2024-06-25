"""_summary_

El cog de musica del bot, viva
"""

import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from yt_dlp import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        self.vc = {}
        
        self.YTDL_OPTIONS = {'format':'bestaudio', 'nonplaylist':'True', "verbose": "False"}
        self.FFMPEG_OPTIONS = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options':'-vn'}
        
        self.EMBED_BLUE = 0x0f00bc
        self.EMBED_GREEN = 0x2abc00
        self.EMBED_RED = 0xbc0000
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
                
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = False
            self.is_playing[id] = False

    def now_playing_embed(self, context, song):
        print("entra embed")
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        print("antes cosas context")
        author = context.author
        avatar = author.avatar.url
        
        print("crear embed")
        embed = discord.Embed(
            title="Lo que suena",
            description=f"[{title}]({link})",
            colour = self.EMBED_BLUE
        )
        print("mas embed")
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"El que la puso: {str(author)}", icon_url=avatar)
        return embed
        
                    
    async def join_vc(self, context, channel):
        id = int(context.guild.id)
        print("join-vc", id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            print(self.vc[id])
            self.vc[id] = await channel.connect()
            print(self.vc[id])
            if self.vc[id] == None:
                await context.send("No me pude conectar, ponte vio choro")
                return
        
        else:
            print("antes de moveto")
            await self.vc[id].move_to(channel)
            
    def search_youtube (self, search):
        print("Entra a search youtube")
        query_string = parse.urlencode({'search_query': search})
        htm_content = request.urlopen('http://www.youtube.com/results?' + query_string)
        search_results = re.findall('/watch\?v=(.{11})', htm_content.read().decode())
        return search_results[0:10]
    
    def extract_youtube (self, url):
        print("entra a extract youtube")
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
            
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'source': info['formats'][0]['url'],
            'title': info['title']
        }
        
    def play_next(self, context):
        id = int(context.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1
            
            song = self.musicQueue[id][self.queueIndex[self.queueIndex[id]]][0]
            message = self.now_playing_embed(context, song)
            coroutine = context.send(embed=message)
            future = run_coroutine_threadsafe(coroutine, self.bot.loop)
            try:
                future.result()
            except:
                pass
            
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(context))
            
        else:
            self.queueIndex[id] += 1
            self.is_playing[id] = False         
        
        
    async def play_music(self, context):
        print("Entra a play music")
        id = int(context.guild.id)
        
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
            print("antes de join_vc")
            await self.join_vc(context, self.musicQueue[id][self.queueIndex[id]][1])
            print("antes de embed")
            song = self.musicQueue[id][self.queueIndex[id]][0]
            #message = self.now_playing_embed(context, song)
            #await context.send(embed=message)
            print("antes de tocar")
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(context))
        else:
            await context.send("No hay canciones perkinaso")
            self.queueIndex[id] += 1
            self.is_playing[id] = False
            
    @commands.command(
        name="play",
        aliases=["p","tocar"],
        help="Reproduce la cancion que se le da como parametro"
    )
    async def play(self, context, *args):
        search = " ".join(args)
        id = int(context.guild.id)
        print("Entra a play")
        try:
            user_channel = context.author.voice.channel
        except:
            await context.send("Conectate a un canal de voz, perkinaso") 
            return
        
        # Que pasa cuando no se entregan argumentos
        if not args:
            if len(self.musicQueue[id]) == 0:
                await context.send("No hay niuna wea para tocar, pon algo")
                return
            
            elif not self.is_playing[id]:
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(context)  
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        
        # Que pasa cuando si se entregan argumentos (se busca una cancion)
        else:
            print("Entra a buscar")
            song = self.extract_youtube(self.search_youtube(search)[0])
            if type(song) == type(True):
                await context.send("No se pudo descargar la cancion, busca otra aweonaso")
                
            else:
                print("Entra a reproducir")
                self.musicQueue[id].append([song, user_channel])
                
                if not self.is_playing[id]:
                    print("Intenta reproducir")
                    await self.play_music(context)
                else:
                    message = "Agregado a la cola"
                    await context.send(message)
            
            
            
    @commands.command(
        name="join",
        aliases=["j","conectar"],
        help="Conecta el bot al canal actual"
    )
    async def join(self, context):
        if context.author.voice:
            userChannel = context.author.voice.channel
            #print(self.vc[context.guild.id])
            await self.join_vc(context, userChannel)
            #print(self.vc[id])
            await context.send(f'Chochetrox se conecta a {userChannel}, biba')
        else:
            await context.send("Necesitas estar conectado a un canal de voz, perkinaso")
            
    @commands.command(
        name="leave",
        aliases=["l","salir"],
        help="Desconecta el bot del canal actual"
    )
    async def leave(self, context):
        id = int(context.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex = 0
        if self.vc[id] != None:
            await context.send("Chochetrox dice chao, conchetumare")
            await self.vc[id].disconnect()
            
async def setup(bot):
    await bot.add_cog(music_cog(bot))