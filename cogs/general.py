import discord
import json
import os
import asyncio
from dotenv import load_dotenv
from random import randint
from discord.ext import commands

class General(commands.Cog):
    load_dotenv("../.env")
    SYSTEMPATH = os.getenv("SYSTEMPATH")
    def __init__(self, client):
        self.client = client

    # Rolls dice (min is 1, max is set by user, usage: ?roll x, (where x is the max)
    @commands.command(brief="Roll a random number!", help="To use this, do ?roll <max roll number> eg. ?roll 20")
    async def roll(self, ctx, max):
        outcome = randint(1, int(max))
        await ctx.send(f"The dice have been rolled, your number is {outcome}")

    @roll.error
    async def roll_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            message = await ctx.send("Sorry, you're missing a required argument. Please look at the following\n```?roll <max number to be rolled> eg. ?roll 5```")
            await asyncio.sleep(5)
            await message.delete(0)

    # Check latency
    @commands.command(brief="Use this to ping the bot!")
    async def ping(self, ctx):
        response = round((self.client.latency * 100), 3)
        await ctx.send(f"Pong! {response}ms!")

def setup(client):
    client.add_cog(General(client))