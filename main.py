import discord
import time
import os
import json
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

def main():
  load_dotenv()
  TOKEN = os.getenv('DISCORD_TOKEN') # Bot Token
  GUILD = os.getenv('DISCORD_GUILD') # Guild
  SYSTEMPATH = os.getenv('SYSTEMPATH') # System Path

  client = commands.Bot(command_prefix='?')
  client.remove_command('help')
  discord.Client.maximum_messages = 2000

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