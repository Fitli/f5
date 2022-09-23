import json
import sys

import requests

import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='.', intents=intents, help_command=None)

with open("config.json") as f:
    conf = json.load(f)
    token = conf["token"]
    channel_id = conf["channel"]

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    check_all.start()
    
@client.event
async def on_message(message):
    await client.process_commands(message)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.channel.send("Unknown command")
    else:
        print(error, file=sys.stderr)

@client.command(name='watch')
async def watch(ctx):
    msg = ctx.message.content
    addr = msg.split(maxsplit=1)[1]
    if len(addr.split()) > 1: #TODO: lepší check
        ctx.message.channel.send("it has to be one valid url!")
    if addr[:7] != "http://" and addr[:8] != "https://":
        addr = "http://" + addr
    
    with open("webs.json", "r") as webs:
        state = json.load(webs)
    
    h = download(addr)
    state[addr] = h
    
    with open("webs.json", "w") as webs:
        json.dump(state, webs)

@client.command(name='check')
async def check(ctx):
    msg = ctx.message.content
    addr = msg.split(maxsplit=1)[1]
    if len(addr.split()) > 1: #TODO: lepší check
        ctx.message.channel.send("it has to be one valid url!")
    if addr[:7] != "http://" and addr[:8] != "https://":
        addr = "http://" + addr
    
    with open("webs.json", "r") as webs:
        state = json.load(webs)
    
    if addr not in state:
        await ctx.message.channel.send(f"I am not watching {addr}")
        return
    
    h = download(addr)
    if h != state[addr]:
        await ctx.message.channel.send(f"{addr} has changed!")
    
        state[addr] = h
        
        with open("webs.json", "w") as webs:
            json.dump(state, webs)
    else:
        await ctx.message.channel.send(f"{addr} has not changed...")

@tasks.loop(seconds=10)
async def check_all():
    message_channel = client.get_channel(channel_id)
    await message_channel.send("test 1")
    
    with open("webs.json", "r") as webs:
        state = json.load(webs)

    for addr in state:
        h = download(addr)
        if h != state[addr]:
            await message_channel.send(f"{addr} has changed!")
            state[addr] = h
    
    with open("webs.json", "w") as webs:
        json.dump(state, webs)


@check_all.before_loop
async def before():
    print("waiting...")
    await client.wait_until_ready()
    print("Finished waiting")


def download(addr):
    r = requests.get(addr)
    if not r.ok:
        print(f"can't reach {addr}")
        return -1
    else:
        return hash(r.text)



client.run(token)
