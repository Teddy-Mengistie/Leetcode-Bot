import discord
import random
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
from threading import Timer
from threading import Thread
import threading
import os
import time
#sync method

#Data base connection initation
cluster = MongoClient(os.environ['MONGO_CLIENT'])
collection = cluster["Bot"]["Leetcode Users Data"]

client = commands.Bot(command_prefix = "&")
client.remove_command("help")
#-------------------------
#-------events------------
#-------------------------
@client.event
async def on_ready():
    print('I am ready.')

@client.event
async def on_command_error(ctx, error):
    messages = ["```diff\n-try again```", "```diff\n-misspelled something?```", "```diff\n-check again```"]
    if isinstance(error, commands.CommandNotFound):
        await ctx.channel.send(random.choice(messages))
        await help(ctx)

#-------------------------
#-------commands----------
#-------------------------

@client.command()
async def user(ctx, user_name):
    j = problems(user_name)
    if(j != -1):
        message = discord.Embed(colour = random.randint(0, 0xffffff))
        message.set_thumbnail(url = avtr(user_name))
        message.set_author(name = user_name.capitalize().replace("_", "").replace("-", ""))
        message.add_field(name = 'Completed Problems', value = j)
        await ctx.channel.send(embed = message)
    else:
        messages = ["```try again```", "```incorrect username```", "```you maybe misspelled something```", "```check again```", "```username... is not responding```"]
        await ctx.channel.send(random.choice(messages))

def problems(user_name):
    my_url = f'http://leetcode.com/{user_name}'
    page = requests.get(my_url)
    soup = BeautifulSoup(page.content, 'lxml')
    #num problems done/1453
    num_probs = soup.get_text().replace("\n", "")
    if("/" in num_probs):
        begin = num_probs.find("Progress")+8
        end = num_probs.find("Solved Question")
        ret = num_probs[begin: end].strip()
        end = ret.find("/")
        return int(ret[0:end])
    else:
        return -1

@client.command(name = "lead")
async def leading(ctx):
    update_message = discord.Embed(colour = random.randint(0, 0xffffff))
    all = collection.find().sort("week", -1)
    x = all.next()
    emojis = ["\U0001F9E0", "\U0001F929", "\U0001F61D", "\U0001F92F", "\U0001F973", "\U0001F60E", "\U0001F632", "\U0001F62F", "\U0001F62E"]
    e = random.choice(emojis)
    update_message.set_thumbnail(url = avtr(x["_id"]))
    update_message.set_author(name = f'************{e} \"{x["_id"]}\" {e}************')
    update_message.add_field(name = 'Problems done', value = x["week"], inline = True)
    update_message.add_field(name = 'Lifetime Problems Done', value = x["problems"]+x["week"], inline = True)
    await ctx.channel.send(embed = update_message)

def avtr(user):
    my_url = f'http://leetcode.com/{user}'
    page = requests.get(my_url)
    soup = BeautifulSoup(page.content, 'lxml')
    num_probs = soup.find(alt = "user avatar")
    return num_probs["src"]

@client.command(name = "reset")
@commands.has_role("leetcode-manager")
async def reset(ctx):
        all = collection.find()
        for x in all:
            b = x["_id"]
            collection.update_many({"_id":b},{"$set":{"problems": x["problems"] + x["week"]}})
            collection.update_many({"_id":b},{"$set":{"week": 0}})
        await ctx.channel.send("```diff\n+Reset Successfully!```")

@client.command(name = "addReq")
async def add_request(ctx, userName):
    m = []
    for r in ctx.channel.guild.roles:
         if(r.name == "leetcode-manager"):
             m = r.members
    if(problems(userName) != -1):
        for x in m:
             await x.send(f'```diff\n-{ctx.author.name.capitalize()} would like to add {userName} to the list!```')
    else:
        await ctx.channel.send("```diff\n-User does not exist!```")

@client.command(name = "add")
@commands.has_role("leetcode-manager")
async def add(ctx, user):
        j = problems(user)
        if(j!=-1):
            collection.insert_one({"_id": user,"username": user,"problems": j, "week":0})
            await ctx.channel.send("```diff\n+Added Successfully!```")
        else:
            await ctx.channel.send("```diff\n-Add unsuccessfull :(```")

@client.command(name = "rm")
@commands.has_role("leetcode-manager")
async def remove(ctx, user):
    collection.delete_one({"_id":user})
    await ctx.channel.send("```diff\n+Removed Successfully!```")

@client.command(name = "board")
async def leaderboard(ctx):
    mess = discord.Embed(colour = random.randint(0, 0xffffff))
    mess.set_author(name = 'Updating...')
    updating = False
    all = collection.find().sort("week", -1)
    board = "```{:^74}\n{:^30}{:^25}{:^19}\n".format("***LEADERBOARD***","users", "prob's done", "total")
    c = 0;
    for x in all:
        if(x["week"] < 0 or x["problems"] + x["week"] < 0):
            updating = True
        board += "{:>4}){:^25}{}{:^25}{}{:^22}\n".format(c+1, x["_id"], ":", x["week"], ":", x["problems"] + x["week"])
        c+=1
    board+="```"
    if(not updating):
        await ctx.channel.send(board)
    else:
        await ctx.channel.send(embed = mess)

@client.command(name = "clrl")
@commands.has_role("leetcode-manager")
async def clr_leet(ctx):
    collection.delete_many({})
    await ctx.channel.send("```diff\n+Cleared Successfully!```")

@client.command(name = "clrm")
@commands.has_permissions(manage_messages = True)
async def clear(ctx, amount=10):
    if amount < 50:
        await ctx.channel.purge(limit=amount)
    else:
        await ctx.channel.purge(limit = 50)

@client.command(name = "help",pass_context=True)
async def help(ctx):
    commands_and_description = ["&user <leetcode username> -- Quick info on the amount of leetcode problems done",
                                "&board -- This shows the current leaderboard rated by the amount of problems done in the current week",
                                "&addReq <leetcode username> -- Requests one of the managers to add this user to the log",
                                "&lead -- shows a card of the stats of the currently leading user in the competition",
                                "&clrm *not required*<specific amount of messages> -- Deleted the amount of messages specified, max = 50, default = 10",
                                "&add <leetcode username> -- This adds the requested username to the log",
                                "&rm <leetcode username> -- This removes a user from the log",
                                "&reset -- resets the leaderboard",
                                "&clrl -- deletes and clears all the users from the log"]
    isManager = False
    i = ctx.message.author.roles
    k = 4
    for j in i:
        if("leetcode-manager" == j.name):
            isManager = True
            k = len(commands_and_description)
    help_message = "```\n"
    for x in range(0, k):
        help_message += commands_and_description[x]
        help_message += "\n\n"
    help_message += "```"
    await ctx.channel.send(help_message)


client.run(os.environ['TOKEN'])
