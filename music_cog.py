"""_summary_

El cog de musica del bot, viva
"""

import discord
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from youtube_dl import YoutubeDL

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        self.vc = {}
        
        self.YTDL_OPTIONS = {'format':'bestaudio', 'nonplaylist':'True'}
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
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = context.author
        avatar = author.avatar_url
        
        embed = discord.Embed(
            title="Lo que suena",
            description=f"[{title}]({link})",
            colour = self.EMBED_BLUE
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"El que la puso: {str(author)}", icon_url=avatar)
        return embed
        
                    
    async def join_vc(self, context, channel):
        id = int(context.guild.id)
        print(id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            print(self.vc[id])
            self.vc[id] = await channel.connect()
            print(self.vc[id])
            if self.vc[id] == None:
                await context.send("No me pude conectar, ponte vio choro")
                return
        
        else:
            await self.vc[id].move_to(channel)
            
    def search_youtube (self, search):
        query_string = parse.urlencode({'search_query': search})
        htm_content = request.urlopen('http://www.youtube.com/results?' + query_string)
        search_results = re.findall('/watch\?v=(.{11})', htm_content.read().decode())
        return search_results[0:10]
    
    def extract_youtube (self, url):
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
        id = int(context.guild.id)
        
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused = False
            
            await self.join_vc(context, self.musicQueue[id][self.queueIndex[id]][1])
            
            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.now_playing_embed(context, song)
            await context.send(embed=message)
            
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(context))
        else:
            await context.send("No hay canciones perkinaso")
            self.queueIndex[id] += 1
            self.is_playing = False
            
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
            await context.send(f'Chochetrox se conecta a {userChannel}')
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