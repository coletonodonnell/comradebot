import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

class Music(commands.Cog):
  load_dotenv("../.env")
  DJ = int(os.getenv('DJ_ROLE'))
  def __init__(self, client):
    self.client = client
    self.SYSTEMPATH = os.getenv("SYSTEMPATH")

  # Voice Stuff:
  # Checks to see if the bot is connected to a voice Channel
  def is_voice_connected(self, ctx):
    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()

  # This downloads the audio, naming it after the Hour, Minute, and Microsecond. This is used to get a guaranteed individual name
  def download_audio(self, link):
    x = datetime.datetime.now() # Initialize datetime
    time = x.strftime("%H%M%f") # Hour, Minute, Microsecond
    title = f'{self.SYSTEMPATH}audio/{time}.mp3' # Setting the fullpath and title
    subprocess.run(['/usr/bin/youtube-dl', '-x', '--audio-format', 'mp3', '-o', title, link]) # Download the video via youtube-dl
    return title

  # Queue system, uses asyncio.Event() and asyncio.Queue(). 
  @staticmethod
  async def queue_system():
    while True: # While loop
      next_queue.clear() # Set the flag to false
      task = await song_queue.get() # Fetch most recent task (this is an array, where the 0th term is the voice_client object, and the second is the path to the video)
      connected = task[0] # Fetch the 1st element 
      path = task[1] # Fetch the 2nd element
      await Music.player_queue(connected, path) # Throw these into player_queue()
      await next_queue.wait() # The flag must be True for the next iteration to continue, this flag is set in player_queue()

  # This is the actual task for the queue system, it plays the audio and when the audio is done playing, it sets the next_queue flag to true so that the while loop in queue_system() can finish
  @staticmethod
  async def player_queue(connected, path):
    connected.play(discord.FFmpegPCMAudio(path)) # Play the audio
    playing = connected.is_playing() # define playing (This should always be true if the above happens without an error)
    while playing == True: # While loop, if playing is true, continue
      playing = connected.is_playing() # Redefine playing, when the audio is done playing (it is set to False) the loop will finish 
      await asyncio.sleep(0.1)
    if os.path.exists(path):
      os.remove(path)
    song_queue.task_done() # This tells the queue that the task has finished completely, and that it can be removed from the dictionary
    next_queue.set() # This sets the next_queue() to True. 

  # Play command, this must have a link 
  @commands.has_role(DJ)
  @commands.command(brief="Use this to play music!", help="Use ?play <YouTube Link>")
  async def play(self, ctx, link):
    if Music.is_voice_connected(self, ctx) == True: # If is_voice_connected() == True then connected = ctx.voice_client
      connected = ctx.voice_client
    else: # Otherwise, please connect 
      channel = ctx.author.voice.channel
      connected = await channel.connect()

    # Download the audio using link
    download = self.download_audio(link)
    await song_queue.put([connected, download]) # Parse it into the queue

  @play.error
  async def play_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()
      
  # Join the voice channel, but don't play anything
  @commands.has_role(DJ)
  @commands.command(brief="This makes the bot join your Voice Channel")
  async def join(self, ctx):
    channel = ctx.author.voice.channel
    connected = await channel.connect()

  @join.error
  async def join_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

  # Leave the voice channel
  @commands.has_role(DJ)
  @commands.command(brief="This makes the bot leave the Voice Channel")
  async def leave(self, ctx):
    await ctx.voice_client.disconnect()

  @leave.error
  async def leave_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

  # Skip the track
  @commands.has_role(DJ)
  @commands.command(brief="Skips the currently playing song")
  async def skip(self, ctx):
    if Music.is_voice_connected(self, ctx) == True:
      connected = ctx.voice_client
      connected.stop()
    else: 
      ctx.send("The bot isn't even connected the voice channel! C'mon...")

  @skip.error
  async def skip_error(ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

  @commands.has_role(DJ)
  @commands.command(brief="Clears the queue.")
  async def clear(self, ctx):
    if Music.is_voice_connected(self, ctx) == True:
      connected = ctx.voice_client
      connected.stop()
      for x in range(song_queue.qsize()):
        connected.stop()
        await song_queue.get() 
        song_queue.task_done()
      remove_files = glob.glob(f'{self.SYSTEMPATH}audio/*.mp3')
      for x in remove_files:
        os.remove(x)

  @clear.error
  async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

def setup(client):
  client.add_cog(Music(client))