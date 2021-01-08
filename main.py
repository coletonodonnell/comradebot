import discord
import time
import os
import os.path
import json
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

def main():
  load_dotenv()
  TOKEN = os.getenv('DISCORD_TOKEN') # Bot Token
  GUILD = os.getenv('DISCORD_GUILD') # Guild
  SYSTEMPATH = os.getenv('SYSTEMPATH') # System Path
  STAFF = int(os.getenv('STAFF_ROLE')) # Staff Role

  files = {"whoswho.json", "starlb.json", "starboard.json"}
  for i in files:
    if os.path.isfile(f"{SYSTEMPATH}{i}") == False:
      f = open(i, "a")
      f.write("{\n}")
      f.close

  client = commands.Bot(command_prefix='?')
  client.remove_command('help')
  discord.Client.maximum_messages = 2000

  @commands.has_role(STAFF)
  @client.command()
  async def load(ctx, extension):
    if os.path.isfile(f"{SYSTEMPATH}cogs/{extension}.py"):
      client.load_extension(f"cogs.{extension}")
    else:
      temp = ""
      for filename in os.listdir(f"{SYSTEMPATH}cogs"):
        if filename.endswith(".py"):
          temp += f"`{filename[:-3]}`\n"
      await ctx.send(f"{extension} doesn't exist, the possible cogs are:\n{temp[:-1]}")

  @commands.has_role(STAFF)
  @client.command()
  async def unload(ctx, extension):
    if os.path.isfile(f"{SYSTEMPATH}cogs/{extension}.py"):
      client.unload_extension(f"cogs.{extension}")
    else:
      temp = ""
      for filename in os.listdir(f"{SYSTEMPATH}cogs"):
        if filename.endswith(".py"):
          temp += f"`{filename[:-3]}`\n"
      await ctx.send(f"{extension} doesn't exist, the possible cogs are:\n{temp[:-1]}")

  @commands.has_role(STAFF)
  @client.command()
  async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")

  # Checks if bot is connected to guild 
  @client.event
  async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to:\n'
        f'{guild.name} (id: {guild.id})'
    )
    
  for filename in os.listdir(f"{SYSTEMPATH}cogs"):
    if filename.endswith(".py"):
      client.load_extension(f"cogs.{filename[:-3]}")
  
  client.run(TOKEN)
main()
