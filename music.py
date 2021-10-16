import asyncio
import youtube_dl
import pafy
import discord
from discord.ext import commands

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            ctx.voice_client.stop()
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

    player={}

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()

        await ctx.send("Je ne suis pas connecté a un salon vocal.")

    @commands.command()
    async def play(self, ctx, *, song=None):
        if song is None:
            return await ctx.send("Vous devez inclure une musique (>play [musique])")

        if ctx.voice_client is None:
            return await ctx.send("Je dois être dans un salon vocal pour faire de la musique.")

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Je recherche la musique cela peut prendre quelques secondes")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Désolé mais je n'ai pas trouvé la musique veuillez essayer avec ma commande de recherche")

            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"Je joue déjà une musique elle a été ajoutée a la liste en position: {queue_len+1}.")

            else:
                return await ctx.send("Désolé je ne peux pas avoir plus de 10musiques dans la liste")

        await self.play_song(ctx, song)
        await ctx.send(f"Je joue actuellement: {song}")

    @commands.command()
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("You forgot to include a song to search for.")

        await ctx.send(f"Je recherche {song} cela peut prendre quelques secondes")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Resultats pour '{song}':", description="*Vous pouvez utiliser une de ces urls pour jouer la musique*\n", colour=ctx.author.color)
        
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Voici les {amount} resultats.")
        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("Il ny'a aucune musique sur la liste pour l'instant")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Je ne joue aucune musique pour l'instant.")

        if ctx.author.voice is None:
            return await ctx.send("Désolé mais vous n'êtes connectés a aucun salon vocal pour l'instant")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("Je ne joue aucune musique")

        poll = discord.Embed(title=f"Vote Skip proposé par:  {ctx.author.name}", description="**80% du salon vocal doivent voter pour passer la musique.**", color=ctx.author.color)
        poll.add_field(name="Skip", value="<a:yes:761533590503948289>")
        poll.add_field(name="Ne aps skip", value="<a:croix:762042127617622027>")
        poll.set_footer(text="Le vote se termine dans 15secondes")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = discord.Embed(title="La musique a été skip avec succés", description="***Vote pour skip la musique effectué avec succés, je skip...***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Le skip a échoué", description="*Le vote pour skip la musique actuelle a échoué.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=discord.Colour.red())

        embed.set_footer(text="Le vote est terminé")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)

@commands.Cog.listener()
async def on_member_join(self, member):
    if member.id in bot.blacklisted_users:
        guild = member.guild
        await guild.ban(member, reason="ce membre à été blacklist")
        db=sqlite3.connect("main.sqlite")
        cursor=db.cursor()
        cursor.execute("SELECT channel_id FROM main WHERE guild_id = {member.guild.id}")
        result=cursor.fetchone()
        if result is None:
            return
        else:
            cursor.execute("SELECT msg FROM main WHERE guild_id = {member.guild.id}")
            result1=cursor.fetchone()
            members=len(list(members.guild.members))
            mention=member.mention
            user=member.name
            guild=member.guild
            embed=discord.Embed(description=str(result1[0]).format(members=members, mention=mention, user=user, guild=guild), color=0xfa8072)
            channel=self.bot.get_channel(id=int(result[0]))
            await channel.send(embed=embed)
