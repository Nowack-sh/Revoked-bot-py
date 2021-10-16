import discord 
from discord.ext import commands, tasks
import random 
import discord.utils
from discord.utils import get
import time
import asyncio
import aiohttp
import textwrap
import aiofiles
from pathlib import Path
import sys
import itertools
import datetime
import re
import traceback
from datetime import timedelta
from random import choice, randint
import os
import json
import pafy
import giphy_client
import youtube_dl
from giphy_client.rest import ApiException
from async_timeout import timeout
from functools import partial
import logging
from music import Player
import sqlite3
import discord_slash

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}/bot\n-----")

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h":3600, "s":1, "m":60, "d":86400}

class TimeConverter(commands.Converter):
    async def convert(ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k]*float(v)
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return time

def isOwner(ctx):
    return ctx.message.author.id == 803686635387879524, 325366800818896896

intents=discord.Intents.default()
intents.members = True

forbidden_channels = [861960696573067275, 849602432119996467]

async def channel_check(ctx):
    if ctx.message.channel.id in forbidden_channels:
        return False
    else:
        return True

def canManageMessages(ctx):
    return ctx.message.author.permissions_in(ctx.message.channel).manage_messages

def canManageNicknames(ctx):
    return ctx.message.author.permissions_in(ctx.message.channel).manage_nicknames

bot = commands.Bot(intents=intents, command_prefix=">", help_command=None)
bot.remove_command("help")
bot.blacklisted_users=[]
bot.ticket_configs={}
players={}

def read_json(filename):
    with open(f"{cwd}/{filename}.json", "r") as file:
        data = json.load(file)
    return data

def write_json(data, filename):
    
    with open(f"{cwd}/{filename}.json", "w") as file:
        json.dump(data, file, indent=4)


page1 = discord.Embed(title="Page d'aide #1", description="Modérations:")
page1.add_field(name="`>blacklist`", value="Ban un membre en l'empêchant de revenir sauf si il est whitlist puis unban.", inline=False)
page1.add_field(name="`>whitelist`", value="Permet de retirer un membre de la blacklist.", inline=False)
page1.add_field(name="`>unban`", value="Débanni un membre.", inline=False)
page1.add_field(name="`>ban`", value="Ban un membre.", inline=False)
page1.add_field(name="`>clear`", value="Supprime un certain nombre de messages.", inline=False)
page1.add_field(name="`>nuke`", value="Supprime et recrée un channel.", inline=False)
page1.add_field(name="`>roleinfo`", value="Affiche les infos d'un rôle.", inline=False)
page1.add_field(name="`>nick`", value="Change le pseudonnyme d'un membre.", inline=False)
page1.add_field(name="`>mute`", value="Rends un membre muet.", inline=False)
page1.add_field(name="`>lock`", value="Empêche tout les membres de parler dans un channel.", inline=False)
page1.add_field(name="`>unlock`", value="Repremets aux membres de parler dans un channel.", inline=False)
page1.add_field(name="`>unmute`", value="Rends la parole à un membre muet.", inline=False)
page2 = discord.Embed(title="Page d'aide #2", description="Fun.")
page2.add_field(name="`>pfc`", value="Pierre feuille ciseaux contre le bot.", inline=False)
page2.add_field(name="`>snipe`", value="Affiche le dernier message supprimé", inline=False)
page2.add_field(name="`>pp`", value="Affiche votre Photo de profil ou celle d'un membre.", inline=False)
page2.add_field(name="`>flip`", value="Lance un pile ou face.", inline=False)
page2.add_field(name="`>say`", value="Fais parler le bot.", inline=False)
page2.add_field(name="`>slap`", value="Simule une claque.", inline=False)
page2.add_field(name="`>kill`", value="Simule un meurtre.", inline=False)
page2.add_field(name="`>hug`", value="Simule un câlin.", inline=False)
page2.add_field(name="`>combine`", value="Combine deux pseudos", inline=False)
page2.add_field(name="`>bvn`", value="Souhaite la bienvenue à un membre", inline=False)
page2.add_field(name="`>fakeban`", value="Faux ban.", inline=False)
page2.add_field(name="`>dm`", value="Envoie un message privé.", inline=False)
page2.add_field(name="`>gayrate`", value="Vous attribue un pourcentage de gaytudee (>gayrate [@lapersonne]) (:).", inline=False)
page3 = discord.Embed(title="Page d'aide #3", description="Support/Extras.")
page3.add_field(name="`>discord`", value="Envoie le serveur de support de Revoked.", inline=False)
page3.add_field(name="`>suggest`", value="Envoie votre suggestion à l'Owner du bot. (Nowack)", inline=False)
page3.add_field(name="`>help`", value="Affiche cette page d'aide.", inline=False)
page3.add_field(name="`>credits`", value="Affiche les credits.", inline=False)
page3.add_field(name="`>invite`", value="Affiche mon lien d'invitation.", inline=False)
page3.add_field(name="`>ping`", value="Affiche la latence du bot.", inline=False)
page3.add_field(name="`>counter`", value="Affiche le nombre de serveurs sur lesquels Revoked se trouve.", inline=False)
page1.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
page2.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
page3.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
page4=discord.Embed(title="Page d'aide #4", description="Musique")
page4.add_field(name="`>join`", value="Rejoin le salon vocal")
page4.add_field(name="`>play`", value="Joue une musique")
page4.add_field(name="`>leave`", value="Quitte le salon vocal")
page4.add_field(name="`>queue`", value="Affiche les musiques qui sont en attente sur la liste")
page4.add_field(name="`>search`", value="Recherche une musique")
page4.add_field(name="`>skip`", value="Effectue un vote pour passer la musique actuelle")
page4.add_field(name="`>pause`", value="Bientôt...")
page4.add_field(name="`>resume`", value="Bientôt...")
page4.add_field(name="`>stop`", value="Bientôt...")
page4.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")

bot.help_pages=[page1, page2, page3, page4]

@bot.command()
@commands.check(channel_check)
async def help(ctx):
    buttons = [u"\u23EA", u"\u2B05", u"\u27A1", u"\u23E9"] # skip to start, left, right, skip to end
    current = 0
    msg = await ctx.send(embed=bot.help_pages[current])
    
    for button in buttons:
        await msg.add_reaction(button)
        
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)

        except asyncio.TimeoutError:
            return print("test")

        else:
            previous_page = current
            if reaction.emoji == u"\u23EA":
                current = 0
                
            elif reaction.emoji == u"\u2B05":
                if current > 0:
                    current -= 1
                    
            elif reaction.emoji == u"\u27A1":
                if current < len(bot.help_pages)-1:
                    current += 1

            elif reaction.emoji == u"\u23E9":
                current = len(bot.help_pages)-1

            for button in buttons:
                await msg.remove_reaction(button, ctx.author)

            if current != previous_page:
                await msg.edit(embed=bot.help_pages[current])

@bot.command(aliases=['bl'])
@commands.check(channel_check)
@commands.has_permissions(ban_members = True)
async def blacklist(ctx, user: discord.Member):
    if ctx.message.author.id == user.id:
        await ctx.send("Hey, tu ne peux pas t'auto blacklist !")
        return

    bot.blacklisted_users.append(user.id)
    data = read_json("blacklist")
    data["blacklistedUsers"].append(user.id)
    write_json(data, "blacklist")
    embed=discord.Embed(title="Blacklist !", description=f"Hey, {user.name} viens d'être blacklist", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.guild.ban(user, reason="Blacklist")
    await ctx.send(embed=embed)

@bot.command()
async def partenariats(ctx, user: discord.Member):
    embed=discord.Embed(title=f"Nouveau partenaire", description=f"Merci à {ctx.author.mention} d'avoir effectué ce partenariats\nLe partenaire: {user.mention}\nLe community manager: {ctx.author.mention}")
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def slap(ctx, user: discord.Member, q="Slap anime"):
    Api_Key='R5bk0NZyp1wVS4S5mV6uYQ2Dnoa97Z85'
    api_instance=giphy_client.DefaultApi()

    try:
        user1=ctx.author.name

        api_responce=api_instance.gifs_search_get(Api_Key, q, limit=5, rating='g')
        uneliste=list(api_responce.data)
        gif=random.choice(uneliste)

        embed=discord.Embed(title=f"{user1} met une claque à {user.name} :raised_back_of_hand:", color=ctx.author.color)
        embed.set_image(url=f'https://media.giphy.com/media/{gif.id}/giphy.gif')
        embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
        await ctx.channel.send(embed=embed)
    except ApiException as e:
        print("Exception lors du contact a l'api")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def hug(ctx, user: discord.Member, q="Hug anime"):
    Api_Key='R5bk0NZyp1wVS4S5mV6uYQ2Dnoa97Z85'
    api_instance=giphy_client.DefaultApi()

    try:
        user1=ctx.author.name

        api_responce=api_instance.gifs_search_get(Api_Key, q, limit=5, rating='g')
        uneliste=list(api_responce.data)
        gif=random.choice(uneliste)

        embed=discord.Embed(title=f"{user1} fais un câlin à {user.name} :hugging:", color=ctx.author.color)
        embed.set_image(url=f'https://media.giphy.com/media/{gif.id}/giphy.gif')
        embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
        await ctx.channel.send(embed=embed)
    except ApiException as e:
        print("Exception lors du contact a l'api")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def kill(ctx, user: discord.Member, q="Kill anime"):
    Api_Key='R5bk0NZyp1wVS4S5mV6uYQ2Dnoa97Z85'
    api_instance=giphy_client.DefaultApi()

    try:
        user1=ctx.author.name

        api_responce=api_instance.gifs_search_get(Api_Key, q, limit=5, rating='g')
        uneliste=list(api_responce.data)
        gif=random.choice(uneliste)

        embed=discord.Embed(title=f"{user1} a tué {user.name} ☠️", color=ctx.author.color)
        embed.set_image(url=f'https://media.giphy.com/media/{gif.id}/giphy.gif')
        embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
        await ctx.channel.send(embed=embed)
    except ApiException as e:
        print("Exception lors du contact a l'api")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def bvn(ctx):
    server = ctx.guild
    numberOfPerson = server.member_count
    serverName = server.name
    embed=discord.Embed(title=f"Bienvenue a toi sur {serverName} !", description=f"{ctx.author.mention} te souhaite la bienvenue parmis nous, nous sommes désormais: {numberOfPerson} <:Stonks:803000703626903634>", color=ctx.author.color)
    embed.set_thumbnail(url="https://cdn.discordapp.com/icons/714937264643506237/a_f9bfa1b24183d4e0b24f10dab474a9cd.gif")
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed, delete_after=15)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def pfc(ctx, valeur: str):
    symboles = ("pierre", "feuille", "ciseaux")
    symboles_short = ("p", "f", "c")
    valeur_bot = random.choice(symboles)
    egalite = False
    if valeur[0].lower() == symboles_short[0]:
        valeur = symboles[0]
        if valeur_bot == "feuille":
            joueur_gagne = False 
        elif valeur_bot == "ciseaux":
            joueur_gagne = True
        else:
            egalite = True
    elif valeur[0].lower() == symboles_short[1]:
        valeur = symboles[1]
        if valeur_bot == "ciseaux":
            joueur_gagne = False
        elif valeur_bot == "pierre":
            joueur_gagne = True
        else:
            egalite = True
    elif valeur[0].lower() == symboles_short[2]:
        valeur = symboles[2]
        if valeur_bot == "pierre":
            joueur_gagne = False
        elif valeur_bot == "feuille":
            joueur_gagne = True
        else:
            egalite = True
    resultat = "égalité" if egalite else f"{ctx.author.name} gagne" if joueur_gagne else f"{ctx.author.name} perd"
    embed = discord.Embed(color=ctx.author.color)
    embed.add_field(name="Résultats", value=f"{ctx.author.name} a choisi {valeur}, et le bot a choisi {valeur_bot}. **{resultat}** !")
    embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command()
@commands.check(channel_check)
@commands.check(isOwner)
async def restart(ctx):
    embed = discord.Embed(
            title=f"{bot.user.name} Redémarre", description="Redémarrage")
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('<a:yes:861945985773469736>')
    await bot.close()

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    embed=discord.Embed(title="Kick !", description=f"{member} a été kick par {ctx.author.mention} pour {reason}", color=ctx.author.color)
    await ctx.send(embed=embed)
    await member.kick(reason=reason)

@bot.command()
async def gayrate(ctx, member: discord.Member):
    pourcent = random.randint(0, 100)
    embedVar = discord.Embed(title="Gay pourcentage.", description=f"{member.mention} est gay à {pourcent}% gay :rainbow_flag:", color=ctx.author.color)
    await ctx.send(embed=embedVar)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
@commands.check(canManageMessages)
async def clear(ctx, num: int):
    await ctx.message.delete()
    await ctx.message.channel.purge(limit=num)
    await ctx.send("clear effectué avec succés <a:yes:861945985773469736>", delete_after=15)

bot.sniped_messages = {}

@bot.event
async def on_message_delete(message):
    bot.sniped_messages[message.guild.id] = (message.content, message.author, message.channel.name, message.created_at)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def snipe(ctx):
    try:
        contents, author, channel_name, time = bot.sniped_messages[ctx.guild.id]
        
    except:
        await ctx.channel.send("Je n'ai rien trouvé a snipe")
        return

    embed = discord.Embed(description=contents, color=ctx.author.color, timestamp=time)
    embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar_url)
    embed.set_footer(text=f"Deleted in : #{channel_name}")

    await ctx.channel.send(embed=embed)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.channel)
async def say(ctx, *texte):
    if "@everyone" in texte or "@here" in texte:
        await ctx.send("Vous ne pouvez pas utiliser de mentions spéciales !")
    else:
        await ctx.send(" ".join(texte))
    await ctx.message.delete()

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def flip(ctx):
    variable=['Pile', 'Face']
    flip=random.choice(variable)
    embed=discord.Embed(title="Résultats:", description=flip, color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.group(invoke_without_command=True)
async def limitelimite(ctx):
    embed=discord.Embed(title="**Voici les règles du jeu.**", description="**Les règles sont simples:**\nVous devez d'abord démarrer une partie (>limite {joueur1} {joueur2} {joueur3} {joueur4} {joueur5} (PS: vous pouvez lancer en étant moins de 5joueurs)\nen lancant la partie vous recevrez des phrases en messages privés c'est les phrases qui devront suivre les phrases du bot", color=ctx.author.color)
    await ctx.send(embed=embed, delete_after=30)

@limitelimite.command()
async def launch(ctx, players: commands.Greedy[discord.Member]):
    phrases=["**Sa vie c'est** ...", "**Grâce à ben laden les** ... **sont heureux**", "**Pour combien d'euros...**", "**Chérie il faut que je te parle de ma terrible addiction à ...**", "**... m'a coûté toute mes économies**", "**La partouze a été interrompue quand dédé est partit se faire retirer ... du réctum**", "**... est la marque d'honneur suprême dans les tribus mongols**", "**Ce soit dans tellement vrai `je collectionne des ...**`", "... **c'est la vie**", "**80% des marriages pour tous se terminent comme ça**", "**L'amour je m'en fou ce que je veux c'est ...**", "**Le gouvernement veut utiliser ... contre les terroristes**", "... **la pire erreur de ma vie**", "**Maman, maman, comment on fait les bébés? ...**", "**Si elle refuse essaye** ...", "... **m'a mit en pls**"]
    choicephrases=random.choice(phrases)
    user1=["**Lepen démontant Hollande avec un gode-ceinture**", "**Merci Jaquie et Michel**", "**Mettre un sticker 'bébé à bord' sur un congelateur**", "**Manger des sushis à Fukishima**", "**Les juifs imberbes**", "**Utiliser une urne funéraire comme cendrier**"]
    user2=["**10 ans d'abstinence**", "**Pouvoir uriner avec son doigt**", "**Les traces du dentier de Brigittte sur le chibre de macron**", "**Les nazis**", "**Manger des cacahuètes pour chier un snickers**", "**La péruque de Donald Trump**", "**Mettre sa bite dans un pain à hot dog**"]
    user3=["**Barbie chômeuse, ken alcoolique", ""]
    for p in players:
        await p.send("__Nouvelle partie ; Voici vos cartes !__")
        for i in range(0, 3):
            card = random.choice(user1)
            await p.send(card)
            user1.remove(card)
    await ctx.send(choicephrases)

@bot.command()
@commands.check(channel_check)
async def combine(ctx, name1, name2): # b'\xfc'
    await ctx.message.delete()
    name1letters = name1[:round(len(name1) / 2)]
    name2letters = name2[round(len(name2) / 2):]
    ship = "".join([name1letters, name2letters])
    emb = (discord.Embed(description=f"{ship}"))
    emb.set_author(name=f"{name1} + {name2}")
    emb.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=emb)

@bot.group(invoke_without_command=True)
async def pub(ctx):
    embed=discord.Embed(title="Voici la pub de revoked:", description=f"▬▬▬▬▬▬▬▬ஜ <a:staff:878767182916505631> REVOKED  <a:staff:878767182916505631>   ஜ▬▬▬▬▬▬▬▬\n<a:monde:878767510000926720>  Hey Toi là ! tu souhaites avoir un bot qui protégeras ton serveur !\n<:fleche:878767572701548565> Ne t’inquiète pas je vais te le présenter \n <a:annonce:878767453595910186> Voici ce que le bot vous propose\n╭・・・・・───══───・・・・・╮\n     <:plus:878767369177169950>  ✩  Un système de Modération \n     <:plus:878767369177169950> ✩  Un anti-Spam\n     <:plus:878767369177169950> ✩  Un anti-Lien\n     <:plus:878767369177169950> ✩  Plusieurs commandes FUN\n     <:plus:878767369177169950>  ✩  Pour + de détail faites >help\n╰・・・・・───══───・・・・・╯\n╭┈˖⋆ ❁───────────────\n┊  ➜ <:partner:878767293490941953> Ton accès  : https://discord.gg/MjFmrYj6G8\n      ➜ <:dl:878767624731889714>  Banniere  : \nhttps://cdn.discordapp.com/attachments/834530205020192830/875697504249851944/standard_59.gif\n╰┄───➤")
    await ctx.send(embed=embed)

@pub.command()
async def raw(ctx):
    embed=discord.Embed(title="Voici la pub de revoked:", description=f"`▬▬▬▬▬▬▬▬ஜ <a:staff:878767182916505631> REVOKED  <a:staff:878767182916505631>   ஜ▬▬▬▬▬▬▬▬\n<a:monde:878767510000926720>  Hey Toi là ! tu souhaites avoir un bot qui protégeras ton serveur !\n<:fleche:878767572701548565> Ne t’inquiète pas je vais te le présenter \n <a:annonce:878767453595910186> Voici ce que le bot vous propose\n╭・・・・・───══───・・・・・╮\n     <:plus:878767369177169950>  ✩  Un système de Modération \n     <:plus:878767369177169950> ✩  Un anti-Spam\n     <:plus:878767369177169950> ✩  Un anti-Lien\n     <:plus:878767369177169950> ✩  Plusieurs commandes FUN\n     <:plus:878767369177169950>  ✩  Pour + de détail faites >help\n╰・・・・・───══───・・・・・╯\n╭┈˖⋆ ❁───────────────\n┊  ➜ <:partner:878767293490941953> Ton accès  : https://discord.gg/MjFmrYj6G8\n      ➜ <:dl:878767624731889714>  Banniere  : \nhttps://cdn.discordapp.com/attachments/834530205020192830/875697504249851944/standard_59.gif\n╰┄───➤`")
    await ctx.send(embed=embed)

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def counter(ctx):
    embed=discord.Embed(title=f"le Bot est présent sur {len(bot.guilds)} serveurs", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command()
async def rainbow(ctx, name):
    guild=ctx.guild
    role= await guild.create_role(name=name)
    color=[0xF4FA58, 0x2EFE2E, 0xFF00BF]
    r=random.choice(color)
    colors=discord.Color(random)
    await role.edit(color=color)
    await asyncio.sleep(3)


@bot.command()
async def rainbowrole(ctx):
    try:
        guild=bot.get_guild(864851923655852040)
        role=guild.get_role(876933273840910376)
        while True:
#            color=[0xF4FA58, 0x2EFE2E, 0xFF00BF]
            color=[0xf16f6f, 0x6f76f1, 0xf1e86f, 0x9f6ff1, 0x6ff17e, 0x6feff1]
            r=random.choice(color)
            colors=discord.Color(r)
            await role.edit(colour=colors)
            await asyncio.sleep(1)
    except Exception as error:
        print(error)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel : discord.TextChannel=None):
    channel = channel or ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send('Channel locked.')

@bot.event
async def on_message(message):
    if "discord.gg/" in message.content.lower():
        guild=[714937264643506237]
        if message.guild.id == guild:
            return
        else:
            await message.delete()
            await message.channel.send("Désolé mais vous ne pouvez pas envoyer de liens d'invitations.")
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(ctx.channel.mention + " ***has been unlocked.***")

status = [f"Je suis sur {len(bot.guilds)}serveurs",
        "Mon préfix de base est: ">"",
		"A votre service","Créer par Nowack",
		"Nowack>ALL","sans beltza rien n'aurait été possible <3",
        ">dsc pour avoir le serveur de support"]

@bot.command()
async def start(ctx, secondes = 5):
	changeStatus.change_interval(seconds = secondes)

@tasks.loop(seconds = 5)
async def changeStatus():
	game = discord.Game(random.choice(status))
	await bot.change_presence(status = discord.Status.dnd, activity = game)

@bot.event
async def on_ready():
    data=read_json("blacklist")
    bot.blacklisted_users=data["blacklistedUsers"]
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.utils.oauth_url(bot.user.id))
    changeStatus.start()
    while True:
        print("Cleared")
        await asyncio.sleep(10)
        with open ("spam_detect.txt", "r+") as file:
            file.truncate(0)

    for file in ["ticket_configs.txt"]:
        async with aiofiles.open(file, mode="a") as temp:
            pass
    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines=await file.readlines()
        for line in lines:
            data=line.split(" ")
            bot.ticket_configs[int(data[0])] = [int(data[1]), int(data[2]), int(data[3])]

@bot.command(aliases=['p', 'q'])
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def ping(ctx, arg=None):
    if arg == "pong":
        await ctx.send("regarde le con il se croit drôle")

    else:
        await ctx.send(f"Ton ping est : {round(bot.latency * 1000)}ms")
        await ctx.message.delete()

@bot.command()
async def on_join(member):
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
            members=len(list(member.guild.members))
            mention=member.mention
            user=member.name
            embed=discord.Embed(title="Bienvenue", description=str(result1[0]).format(members=members, mention=mention, user=user, guild=guild))
            embed.set_thumbnail(url=f"{member.avatar_url}")
            embed.set_author(name=f"{member.name}", icon_url=f"{member.avatar_url}")
            embed.footer(text=f"{member.guild}", icon_url=f"{member.guild.icon_url}")
            embed.timestamp=datetime.datetime.utcnow()

            channel=bot.get_channel(id=int(result[0]))

            await channel.send(embed=embed)

@bot.group(invoke_without_command=True)
async def welcome(ctx):
    await ctx.send(f"Voici la listes de commandes de configurations disponnibles:\n>welcome channel <#nom du channel>\n>welcome text <message de bienvenue>")

@welcome.command()
async def channel(ctx, channel:discord.TextChannel):
    if ctx.message.author.guild_permissions.manage_messages:
            db=sqlite3.connect("main.sqlite")
            cursor=db.cursor()
            cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}")
            result=cursor.fetchone()
            if result is None:
                sql=("INSERT INTO main(guild_id, channel_id) VALUES(?,?)")
                val=(ctx.guild.id, channel.id)
                await ctx.send(f"Le channel a bien été mit sur {channel.mention}")
            elif result is not None:
                sql=("UPDATE main SET channel_id = ? WHERE guild_id = ?")
                val=(channel.id, ctx.guild.id)
                await ctx.send(f"Le channel a bien été mit à jour sur {channel.mention}")
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            db.close()

@welcome.command()
async def text(ctx, *, text):
    if ctx.message.author.guild_permissions.manage_messages:
            db=sqlite3.connect("main.sqlite")
            cursor=db.cursor()
            cursor.execute(f"SELECT msg FROM main WHERE guild_id = {ctx.guild.id}")
            result=cursor.fetchone()
            if result is None:
                sql=("INSERT INTO main(guild_id, msg) VALUES(?,?)")
                val=(ctx.guild.id, text)
                await ctx.send(f"Le message a bel et bien été mit sur `{text}`")
            elif result is not None:
                sql=("UPDATE main SET msg = ? WHERE guild_id = ?")
                val=(text, ctx.guild.id)
                await ctx.send(f"Le message a bel et bien été mit a jour sur `{text}`")
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            db.close()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        message = "**La commande est actuellement en cool down veuillez réessayer dans {:.2f}s**".format(error.retry_after)
        await ctx.send(message)
    if isinstance(error, commands.CommandNotFound):
        embed=discord.Embed(title="CommandNotFound <a:non:861947039918850048>", description="Mmmh, es-tu sur d'avoir bien écrit la commande ? car je ne la trouve pas.", color=ctx.author.color)
        await ctx.send(embed=embed, delete_after=6)
    if isinstance(error, commands.MissingRequiredArgument):
        embed=discord.Embed(title="MissingRequiredArgument <a:non:861947039918850048>", description="Mmmh, Il manque un argument.", color=ctx.author.color)
        await ctx.send(embed=embed, delete_after=6)
    elif isinstance(error, commands.MissingPermissions):
        embed=discord.Embed(title="MissingPermissions <a:non:861947039918850048>", description="Mmmh, il me semble que tu n'as pas la permission d'effectuer cette commande.", color=ctx.author.color)
        await ctx.send(embed=embed, delete_after=6)
    elif isinstance(error, commands.CheckFailure):
        embed=discord.Embed(title="CheckFailure <a:non:861947039918850048>", description="Mmmh, désolé mais vous ne pouvez pas faire cela", color=ctx.author.color)
        await ctx.send(embed=embed, delete_after=6)
    if isinstance(error.original, discord.Forbidden):
        embed=discord.Embed(title="discord.Forbidden <a:non:861947039918850048>", description="Mmmh, Je ne peux pas faire ça.", color=ctx.author.color)
        await ctx.send(embed=embed, delete_after=6)

@bot.command()
async def Hey(ctx):
    await ctx.send("Hey")

@bot.command(aliases=['pm', 'mp'])
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def dm(ctx, user: discord.Member, *, texte):
    text = "".join(texte)
    await user.send(text)
    embed=discord.Embed(title=f"Message envoyé avec succés à {user} <a:yes:861945985773469736>", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def verification(ctx, photo):
    guild=ctx.guild
    channel = await guild.create_text_channel('🌠・vérification')
    embed=discord.Embed(title=f"Vérification", description=f"Bienvenue sur {ctx.guild.name} pour avoir accés au reste des channels veuillez cliquer sur la réaction ci dessous.", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    embed.set_image(url=photo)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    msg=await channel.send(embed=embed)
    perms = discord.Permissions(send_messages=True, read_messages=True)
    role = await guild.create_role(name="✅", colour=discord.Colour(0xfffff), permissions=perms)
    await msg.add_reaction("<a:yes:861945985773469736>")
#            await bot.add_roles(user, role)

#@bot.event()
#async def on_reaction_add(ctx):
#    if ctx.message.id in messages_verif.keys():
#        # add role ctx_member messages_verif[ctx.message.id]

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 10, commands.BucketType.channel)
async def suggest(ctx, *, texte):
    user = bot.get_channel(864864271166865439)
    channel=bot.get_user(803686635387879524)
    embed = discord.Embed(
            title="**Nouvelle Suggestion !** :", url = "https://discord.gg/candyisland")
    embed.add_field(name='Suggestion :', value=texte, inline=False)
    embed.set_author(name = ctx.
    
    author.name, icon_url = ctx.author.avatar_url)
    await ctx.message.add_reaction('<a:yes:861945985773469736>')
    await ctx.author.send("Ta suggestion a bien été envoyée a Nowack <a:yes:861945985773469736>")
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await user.send(embed=embed)
    await channel.send(f"Nouvelle suggestion dans #{user.name}")

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
@commands.has_permissions(ban_members = True)
async def ban(ctx, user : discord.User, *, reason = "Aucune raison n'a été donnée"):
	await ctx.guild.ban(user, reason = reason)
	embed = discord.Embed(title = "**Ban !**", description = "Le marteau du bannissement a frappé", color=ctx.author.color)
	embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
	embed.add_field(name = "Membre banni", value = user.name, inline = True)
	embed.add_field(name = "Pour:", value = reason, inline = True)
	embed.add_field(name = "Par:", value = ctx.author.name, inline = True)
	await ctx.send(embed = embed)

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
@commands.has_permissions(ban_members = True)
async def fakeban(ctx, user : discord.User, *, reason = "Aucune raison n'a été donnée"):
#	await ctx.guild.ban(user, reason = reason)
	embed = discord.Embed(title = "**Ban !**", description = "Le marteau du bannissement a frappé", color=ctx.author.color)
	embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
	embed.add_field(name = "Membre banni", value = user.name, inline = True)
	embed.add_field(name = "Pour:", value = reason, inline = True)
	embed.add_field(name = "Par:", value = ctx.author.name, inline = True)
	await ctx.send(embed = embed)

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def pp(ctx, avamember: discord.Member=None):
    try:
        user_avatar_url = avamember.avatar_url
        user_name= avamember.display_name
    except:
        user_avatar_url = ctx.author.avatar_url
        user_name = ctx.author.display_name
    embed=discord.Embed(title=f"Voici la photo de profil de {user_name} !", color=ctx.author.color)
    embed.set_image(url=f"{user_avatar_url}")
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command(name='unban')
@commands.check(channel_check)
@commands.has_permissions(ban_members = True)
async def _unban(ctx, id: int):
    user = await bot.fetch_user(id)
    await ctx.guild.unban(user)
    embed=discord.Embed(title="Unban !", description=f"Quelqu'un a été pardonné.", color=ctx.author.color)
    embed.add_field(name  = "Par:", value = ctx.author.name, inline = True)
    embed.add_field(name = "Membre débanni", value = user.name, inline = True)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command(aliases=['ri', 'role'])
@commands.check(channel_check)
async def roleinfo(ctx, *, role: discord.Role): # b'\xfc'
    await ctx.message.delete()
    guild = ctx.guild
    since_created = (ctx.message.created_at - role.created_at).days
    role_created = role.created_at.strftime("%d %b %Y %H:%M")
    created_on = "{} ({} days ago)".format(role_created, since_created)
    users = len([x for x in guild.members if role in x.roles])
    if str(role.colour) == "#000000":
        colour = "default"
        color = ("#%06x" % random.randint(0, 0xFFFFFF))
        color = int(colour[1:], 16)
    else:
        colour = str(role.colour).upper()
        color = role.colour
    em = discord.Embed(colour=color)
    em.set_author(name=f"Name: {role.name}"
    f"\nRole ID: {role.id}")
    em.add_field(name="Users", value=users)
    em.add_field(name="Mentionable", value=role.mentionable)
    em.add_field(name="Hoist", value=role.hoist)
    em.add_field(name="Position", value=role.position)
    em.add_field(name="Managed", value=role.managed)
    em.add_field(name="Colour", value=colour)
    em.add_field(name='Creation Date', value=created_on)
    em.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=em)

@bot.command()
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
@commands.check(canManageNicknames)
async def nick(ctx, member: discord.Member, *, nickname: str=None):
    await member.edit(nick=nickname)
    embed = discord.Embed(color=ctx.author.color, title="Changement de pseudo", description=f"Changement de pseudo pour {member.mention} bien effectué.")
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command(aliases=['wl'])
@commands.check(channel_check)
@commands.has_permissions(ban_members = True)
async def whitelist(ctx, id: int):
    bot.blacklisted_users.remove(id)
    data = read_json("blacklist")
    data["blacklistedUsers"].remove(id)
    write_json(data, "blacklist")
    user = await bot.fetch_user(id)
    embed=discord.Embed(title="Unblacklist !", description=f"Hey, {user.display_name} viens d'être unblacklist (n'oubliez pas d'unban)", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send("Whitelisted")

async def getMutedRole(ctx):
    roles = ctx.guild.roles
    for role in roles:
        if role.name == "Muted":
            return role
    
    return await createMutedRole(ctx)

async def createMutedRole(ctx):
    mutedRole = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(send_messages = False, speak = False), reason = "Creation du role Muted pour mute des gens.")
    for channel in ctx.guild.channels:
        await channel.set_permissions(mutedRole, send_messages = False, speak = False)
    return mutedRole

@bot.command()
@commands.check(channel_check)
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member : discord.Member, *, reason = "Aucune raison n'a été renseigné"):
    mutedRole = await getMutedRole(ctx)
    await member.add_roles(mutedRole, reason = reason)
    embed=discord.Embed(title="Mute !", description=f"{member.mention} a été mute pour {reason} avec succés <a:yes:861945985773469736>", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)
    await ctx.message.delete()

@bot.command()
@commands.check(channel_check)
@commands.has_permissions(manage_messages=True)
async def nuke(ctx, channel: discord.TextChannel = None):
    if channel == None: 
        await ctx.send("Vous n'avez pas mentionner un channel.")
        return

    nuke_channel = discord.utils.get(ctx.guild.channels, name=channel.name)

    if nuke_channel is not None:
        new_channel = await nuke_channel.clone(reason="Ce channel a été nuke.")
        await nuke_channel.delete()
        await new_channel.send(f"Ce channel a été nuke. avec succés par {ctx.author.name} <a:yes:761533590503948289>")
        await ctx.send("Le channel a été nuke avec succés. <a:yes:761533590503948289>")

    else:
        await ctx.send(f"Aucun channel nommé {channel.name} n'as été trouvé.")

@bot.command()
@commands.check(channel_check)
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member : discord.Member, *, reason = "Aucune raison n'a été renseigné"):
    mutedRole = await getMutedRole(ctx)
    await member.remove_roles(mutedRole, reason = reason)
    embed=discord.Embed(title="Unmute !", description=f"{member.mention} a été unmute avec succés <a:yes:861945985773469736>", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.message.delete()
    await ctx.send(embed=embed)@bot.command()

@bot.command()
@commands.check(channel_check)
async def invite(ctx):
    embed=discord.Embed(title="Clique ici pour m'inviter.", url="https://discord.com/api/oauth2/authorize?client_id=870287430366945350&permissions=8&scope=bot", color=ctx.author.color)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
@commands.check(channel_check)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def credits(ctx):
    author = ctx.message.author

    embed = discord.Embed(
    title="**Credits**", description="Merci à:", color=ctx.author.color)

    embed.add_field(name='Beltza', value="qui m'a aidé pour plusieurs commandes", inline=False)
    embed.add_field(name='Xernes', value="Premier bug hunter de Revoked", inline=False)
    embed.add_field(name='Bynuti', value="(discord.gg/candyisland 👀)", inline=False)
    embed.add_field(name='Killa', value="Pour avoir été une des premières à ajouter le bot", inline=False)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")

    await ctx.send(embed=embed)

@bot.command()
async def infos(ctx):
    embed=discord.Embed(title="Informations sur Revoked", color = ctx.author.color)
    embed.add_field(name="Version de python:",value="Python 3.9.5", inline=False)
    embed.add_field(name="Version de discord.py:", value="Discord.py v0.0.15", inline=False)
    embed.set_footer(icon_url="https://cdn.discordapp.com/avatars/803686635387879524/a_3a0a113ff125aafbadf55cbb1b879a33.gif?size=1024", text=f"・Revoked crow bot by Nowack")
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    channel=ctx.author.voice.channel
    await channel.connect()

@bot.command(aliases=['discord'])
async def dsc(ctx):
    embed=discord.Embed(title="Clique ici pour avoir le lien d'invitation du support", url="https://discord.gg/n5mA3SxeRg", color=ctx.author.color)
    await ctx.author.send(embed=embed)
    await ctx.send("Vous avez reçu le lien du serveur de support en message privé.")

@bot.command()
@commands.check(isOwner)
async def annonce(ctx, *, r):
    embed=discord.Embed(title="Statut du bot: <a:satourne:861946343420461076>", description=r, color=ctx.author.color)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.id != bot.user.id and str(payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = bot.ticket_configs[payload.guild_id]

        if payload.message_id == msg_id:
            guild = bot.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_channel = await category.create_text_channel(f"ticket-{payload.member.display_name}", topic=f"Ticket pour {payload.member.display_name}.", permission_synced=True)
            
            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            await ticket_channel.send(f" Pour Fermer le ticket veuillez écrire dans le channel `>close`")

            try:
                await bot.wait_for("message", check=lambda m: m.channel == ticket_channel and m.author == payload.member and m.content == ">close", timeout=3600)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()

@bot.command()
async def configure_ticket(ctx, msg: discord.Message=None, category: discord.CategoryChannel=None):
    if msg is None or category is None:
        await ctx.channel.send("Je n'arrive pas a configurer le ticket il manque des argument (>configure_ticket [id du message] [id de la catégories de channels])")
        return

    bot.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id] # this resets the configuration

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)
                
    await msg.add_reaction(u"\U0001F3AB")
    await ctx.channel.send("Ticket configuré avec succés")

@bot.command()
async def ticket_config(ctx):
    try:
        msg_id, channel_id, category_id = bot.ticket_configs[ctx.guild.id]
    except KeyError:
        await ctx.channel.send("Vous n'avez pas configuré le systéme de ticket")
    else:
        embed=discord.Embed(title="Configuration du systéme de ticket", color=ctx.author.color)
        embed.description=f"**Reaction Message ID** : {msg_id}\n"
        embed.description=f"**Ticket Category** : {category_id}\n"

        await ctx.channel.send(embed=embed)

bot.add_cog(Player(bot))
bot.run("ODcwMjg3NDMwMzY2OTQ1MzUw.YQKkVA.FBpatt_LKLc3zxncFirEnmGyoZU") 
