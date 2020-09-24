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

    @commands.command()
    async def help(self, ctx):
        playCategory = """
?play <search>
    Plays the top search result from youtube.

?join
    Make the bot join the call.

?leave
    Make the bot leave the call. 

?skip
    Make the bot skip the current playing song. 

?clear
    Clear the queue.

Note:
    None of these commands work while a playlist is active."""

        playlistCategory = """
?playlist start <playlist name>
    Starts a playlist with an optional vote depending on how many people are in the voice call.

?playlist stop
    Stops a playlist from playing with an optional vote depending on how many people are in the voice call.

?playlist create <playlist name>
    Create a playlist. Playlists must be one word long. Playlists will be saved as one 

?playlist delete <playlist name>
    Delete a playlist.

?playlist add <playlist name> <youtube link>
    Adds a youtube link to a playlist. Must be either a `https://www.youtube.com/watch?v=id` or `https://youtu.be/id` link.

?playlist remove <playlist name> <youtube link>
    Remove a youtube link from a playlist. Use ?playlist list <playlist name> to get every link in the playlist.

?playlist list <playlist name>
    Lists every link in a playlist. 

?playlist add_contributor <playlist_name> @TheirUsername#0001
    Add a contributor to a playlist, they can add and remove songs. They must be pinged/mentioned for it to count.

?playlist remove_contributor <playlist_name> @TheirUsername#0001
    Remove a contributor from a playlist. They must be pinged/mentioned for it to count. 

?playlist list_contributor <playlist_name>
    List every contributor in a playlist. 

?playlist listall
    List every playlist in the guild."""

        generalCategory = """
?ping
    Ping the bot.

?roll <number>
    Roll  a number between 1 and the selected number. 
    
?starlb
    Display the starboard leaderboard.
"""

        await ctx.author.send(f"General:\n```{generalCategory}```Play:\n```{playCategory}```\nPlaylist:```{playlistCategory}```")
        await ctx.message.add_reaction("✅")

def setup(client):
    client.add_cog(General(client))