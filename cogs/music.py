import subprocess
import discord
import datetime
import json
import os
import os.path
import glob
import asyncio
from random import randint
from youtube_search import YoutubeSearch
from os import path
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get

class Music(commands.Cog):
  load_dotenv("../.env")
  DJ = int(os.getenv('DJ_ROLE'))
  def __init__(self, client):
    #?general
    self.client = client
    self.SYSTEMPATH = os.getenv("SYSTEMPATH")
    self.PLAYLIST_MINIMUM = int(os.getenv("PLAYLIST_VOTE_MINIMUM"))
    self.audio_share = asyncio.Lock()

    #?play
    self.play_song_queue = asyncio.Queue()
    self.play_next_queue = asyncio.Event() 
    self.play_lock = asyncio.Event()
    self.play_lock.set()
    self.client.loop.create_task(self.play_queue_system())

    #?playlist
    self.playlist_trigger = asyncio.Lock()

#general section:
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
  
  # Takes the count of the amount of people in the voice call, minus the bot and the user who called the command.
  def connected_count(self, ctx):
    channel = ctx.author.voice.channel
    count = len(channel.members)
    if self.is_voice_connected(ctx) == True:
      count -= 2
    else:
      count -= 1
    return count

#?playlist section:
  # The Queue System
  # This is a heavily modified version of the play_queue_system as seen below
  # As the ?play command was an individual put to the queue, I needed to find a way to use the queue
  # sections and still have a way to both produce and consume on an individual basis of ?playlist being called
  # This is the solution.
  async def playlist_queue_system(self, playlist, connected):
    self.playlist_song_queue = asyncio.Queue(maxsize=2) # Set the queue
    self.playlist_next_queue = asyncio.Event() # Set theA event
    with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json") as x:
      data = json.load(x) # load the json file that corresponds to playlist
      length = len(data["playlist_data"]) # take the length of the playlist as length
      song_range = [0, length - 1] # finding the range
      old_choice = -1 # setting the old_choice to something the first choice couldn't equal (-1)
      while self.playlist_trigger.locked(): # While playlist_trigger is locked, do the following:
        self.playlist_next_queue.clear() # lock the event 
        while self.playlist_song_queue.full() != True: # This fills the queue on the first iteration, then after that it fills once the queue has taken a song
          choice = randint(song_range[0], song_range[1])
          if choice == old_choice: # Guarantees a song won't play twice
            choice += 1
            if choice > song_range[1]:
              choice -= 2
          old_choice = choice # Set old_choice as the last choice
          link = data["playlist_data"][choice] # Find the link
          path = self.download_audio(link) # Find the path
          await self.playlist_song_queue.put([connected, path]) # Insert these into the queue
        task = await self.playlist_song_queue.get() # Get the queue object
        connected  = task[0] # define the first grabbed queue object, connected
        path = task[1] # define the second grabbed queue object, path
        await self.playlist_queue(connected, path) # Feed these to the consumer, playlist_queue()
        await self.playlist_next_queue.wait() # Wait for the playlist_queue method to finish up
      # Once the above function has ended (the playlist has been ended) do the following
      for x in range(self.playlist_song_queue.qsize()):  # flush the song_queue object
        connected.stop() # stop the connection
        await self.playlist_song_queue.get() # get each of the remaining queue objects
        self.playlist_song_queue.task_done() # dispose of them
      remove_files = glob.glob(f'{self.SYSTEMPATH}audio/*.mp3') # find all .mp3 files in the audio directory
      for x in remove_files: # Remove them all
        os.remove(x)
      self.play_lock.set() # Let people use ?play once more

  async def playlist_queue(self, connected, path):
    connected.play(discord.FFmpegPCMAudio(source=path, executable="/usr/bin/ffmpeg")) # I opted for FFmpegPCMAudio over FFmpegAudio as it just wasn't working
    playing = connected.is_playing() # returns true if playing
    while playing:
      playing = connected.is_playing()
      await asyncio.sleep(0.1)
    if os.path.exists(path): # Delete audio when done
      os.remove(path)
    self.playlist_song_queue.task_done() # Complete the task
    self.playlist_next_queue.set() # set the event
        
  async def playlist_wait(self, ctx, playlist): # An extra function that is called by playlist_check so code isn't repeated. 
    if self.audio_share.locked() == False and self.play_song_queue.empty() == True: # Basically, if ?play isn't playing
      self.play_lock.clear() # Lock ?play
      if self.is_voice_connected(ctx) == True: # if the bot is connected, then just use that connected object
        connected = ctx.voice_client
      else: # if the bot isn't please connect
        channel = ctx.author.voice.channel
        connected = await channel.connect()
      await self.playlist_trigger.acquire() # startup the playlist trigger
      self.client.loop.create_task(self.playlist_queue_system(playlist, connected)) # start the loop
    else: # Does the above, but waits for ?play to end.
      await ctx.send("Sorry, audio is already playing, but I have locked it for you! Wait for it to end, then the playlist will begin!")
      self.play_lock.clear() # Lock ?play
      lock_test = self.audio_share.locked() # Test 1
      queue_test =  self.play_song_queue.empty() # Test 2
      while True: # Loop until those are finished
        if lock_test == False:
          if queue_test == True:
            break
        lock_test = self.audio_share.locked()
        queue_test =  self.play_song_queue.empty()
        await asyncio.sleep(0.5)
      await self.playlist_trigger.acquire() # startup the playlist trigger
      self.client.loop.create_task(self.playlist_queue_system(playlist, connected)) # start the loop

  async def playlist_check(self, ctx, playlist, count, vote = False): # The core determining logic for the playlist
    if vote == True: # if there is a vote, wait for it
      minimum_vote = round(0.50 * count) + 2 # take half of the call, then add 2, 1 for the starter, the other for the auto bot addition.
      vote_message = await ctx.send(f"Detected more than {self.PLAYLIST_MINIMUM} users (not including the playlist started and bot) in the voice call. I need {minimum_vote} amount of votes to start the playlist (including playlist starter.)")
      await vote_message.add_reaction("✅") # add the check mark
      def playlist_vote_check(reaction, user): # the check
        if str(reaction) == "✅" and reaction.count == minimum_vote:
          return True
      try:
        voteTester = await self.client.wait_for('reaction_add', timeout=120.0, check=playlist_vote_check) # The check
      except asyncio.TimeoutError: # Timeout after 120 seconds
        await vote_message.delete()
        await ctx.send("Sorry, not enough votes within 2 minutes.")
      else: # if not timeout and it succeeded, then do the following
        await self.playlist_wait(ctx, playlist) # call playlist_wait()
    else: # if there isn't a vote, call playlist_wait()
      await self.playlist_wait(ctx, playlist)

  @commands.has_role(DJ)
  @commands.group()
  # ?playlist group.
  async def playlist(self, ctx): 
    if ctx.invoked_subcommand is None:
        message = await ctx.send("Invalid playlist command!")
        await asyncio.sleep(15)
        await message.delete()

  @playlist.error 
  # Error detection for ?playlist
  async def playlist_error(self, ctx, error): 
    if isinstance(error, commands.MissingRole): # if missing DJ role for any ?playlist command, raise the following:
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

  @playlist.command()
  # Start a playlist
  async def start(self, ctx, playlist): 
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"): # if playlist exist
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json") as x:
        data = json.load(x)
        if data["playlist_data"]: # checks if the playlist has data in it. 
          count = self.connected_count(ctx) # count is equal to amount of people in call minus 2 at max
          if count >= self.PLAYLIST_MINIMUM: # if count is >= playlist_minimum vote then do the following
            await self.playlist_check(ctx, playlist, count, vote=True) # pass in vote = True
          else:
            await self.playlist_check(ctx, playlist, count) # Don't pass in vote = True
        else:
          message = await ctx.send(f"`{playlist.lower()}` is empty, please add youtube links to it before attempting to play it.")
          await asyncio.sleep(15)
          await message.delete()
    else: # Do the following if playlist doesn't exist
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(10)
      await message.delete()

  @playlist.command()
  async def stop(self, ctx): # Starts a vote to stop a playlist currently running. 
    if self.playlist_trigger.locked():
      count = self.connected_count(ctx)
      if count >= self.PLAYLIST_MINIMUM:
        minimum_vote = round(0.50 * count) + 2
        vote_message = await ctx.send(f"Detected more than {self.PLAYLIST_MINIMUM} users (not including the vote caller and the bot) in the voice channel. I need {minimum_vote} amount of votes to stop the playlist (including the vote starter.)")
        await vote_message.add_reaction("✅")
        def playlist_vote_check(reaction, user):
          if str(reaction) == "✅" and reaction.count == minimum_vote:
            return True
        try:
          voteTester = await self.client.wait_for('reaction_add', timeout=120.0, check=playlist_vote_check)
        except asyncio.TimeoutError:
          await vote_message.delete()
          await ctx.send("Sorry, not enough votes within 2 minutes.")
        else:
          if self.is_voice_connected(ctx) == True:
            connected = ctx.voice_client
            connected.stop()
          await ctx.send("Successfully stopped the playlist.")
          self.playlist_trigger.release()
      else:
        if self.is_voice_connected(ctx) == True:
          connected = ctx.voice_client
          connected.stop()
        await ctx.send("Successfully stopped the playlist.")
        self.playlist_trigger.release()
    else:
      message = await ctx.send("No playlist is being queued or is playing right now.")
      await asyncio.sleep(20)
      await message.delete()

  @playlist.command()
  async def create(self, ctx, playlist): # Create a playlist
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      message = await ctx.send(f"`{playlist.lower()}` already exists! Playlists are case insensitive and global, please choose another name.")
      await asyncio.sleep(15)
      await message.delete()
    else:
      json_data = {
        "owner": ctx.author.id,
        "contributors": [],
        "playlist_data": []
      }
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as x:
        data = json.dumps(json_data, indent=4)
        x.write(data)
      await ctx.send(f"Successfully created the playlist `{playlist.lower()}.`")

  @playlist.command()
  async def add(self, ctx, playlist, addition): # Add songs to a playlist
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        length = len(data["contributors"])
        confirmation = False
        for i in range(length):
          if data["contributors"][i] == ctx.author.id:
            confirmation = True
        if ctx.author.id == data["owner"] or confirmation == True:
          if addition.startswith("https://youtu.be/") or addition.startswith("https://www.youtube.com/watch"):
            data["playlist_data"].append(addition)
            with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as b:
              new_data = json.dumps(data, indent=4)
              b.write(new_data)
              b.close()
              await ctx.send(f"Successfully added `{addition}` to `{playlist.lower()}`")
          else:
            message = await ctx.send("Sorry that isn't a valid YouTube link. Please format them as either:\n1. `https://youtu.be/id`\n2. `https://www.youtube.com/watch?v=id`")
            await asyncio.sleep(15)
            await message.delete()
        else:
          message = await ctx.send(f"You don't own or contribute to `{playlist.lower()}`, are you sure you entered the right name?")
          await asyncio.sleep(15)
          await message.delete()
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()

  @playlist.command()
  async def remove(self, ctx, playlist, removal): # Remove songs from a playlist
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        length = len(data["contributors"])
        confirmation = False
        for i in range(length):
          if data["contributors"][i] == ctx.author.id:
            confirmation = True
        if ctx.author.id == data["owner"] or confirmation == True:
          length = len(data["playlist_data"])
          confirmation = False
          result = []
          for i in data["playlist_data"]:
            if i != removal:
              result.append(i)
            if i == removal:
              confirmation = True
          data["playlist_data"] = result
          if confirmation == False:
            message = await ctx.send("Couldn't find and delete that entry, did you enter it correctly?")
            await asyncio.sleep(15)
            await message.delete()
          else:
            with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as b:
                new_data = json.dumps(data, indent=4)
                b.write(new_data)
                b.close()
            message = await ctx.send(f"Successfully removed `{removal}` from `{playlist}`!")
        else:
          message = await ctx.send(f"You don't own or contribute to `{playlist.lower()}`, are you sure you entered the right name?")
          await asyncio.sleep(15)
          await message.delete()
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()

  @playlist.command()
  async def list(self, ctx, playlist):
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json") as x:
        data = json.load(x)
        if data["playlist_data"]:
          embed = discord.Embed(color = 0xa3be8c)
          playlist_data = '\n'.join(data["playlist_data"])
          embed.add_field(name=f"{playlist} Data:", value=playlist_data)
          await ctx.send(embed=embed)
        else:
          message = await ctx.send(f"`{playlist.lower()}` is empty. ")
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()
      
  @playlist.command()
  async def add_contributor(self, ctx, playlist, addition: discord.User): # add contributor to a playlist
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        if ctx.author.id == data["owner"]:
          length = len(data["contributors"])
          if length:
            confirmation = False
            for i in range(length):
              if data["contributors"][i] == addition.id:
                confirmation = True
            if confirmation == True:
              message = await ctx.send("That user already is a contributor")
              await asyncio.sleep(15)
              await message.delete()
            else:
              data["contributors"].append(addition.id)
              with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as b:
                new_data = json.dumps(data, indent=4)
                b.write(new_data)
                b.close()
              await ctx.send("Contributor successfully added!")
          else:
            data["contributors"].append(addition.id)
            with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as b:
              new_data = json.dumps(data, indent=4)
              b.write(new_data)
              b.close()
            await ctx.send("Contributor successfully added!")
        else:
          message = await ctx.send(f"You don't own `{playlist.lower()}`, are you sure you entered the right name?")
          await asyncio.sleep(15)
          await message.delete()
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()

  @add_contributor.error
  async def add_contributor_error(self, ctx, error):
    if isinstance(error, commands.BadArgument):
      message = await ctx.send(f"{error}. Are you mentioning the contributor...?\n```?playlist add_contributor <playlist name> @TheContributor#0001```")
      await asyncio.sleep(15)
      await message.delete()

  @playlist.command()
  async def remove_contributor(self, ctx, playlist, removal: discord.User): # remove contributor from a playlist 
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        if ctx.author.id == data["owner"]:
          length = len(data["contributors"])
          if length == 0:
            message = await ctx.send(f"Sorry there isn't any contributors on `{playlist.lower()}`")
          else:
            confirmation = False
            for i in range(length):
              if data["contributors"][i] == removal.id:
                data["contributors"].remove(removal.id)
                confirmation = True
            if confirmation == False:
              message = await ctx.send("Sorry, that isn't a valid contributor, please use the following:\n```?playlist remove_contributor <the user ping>``` if you don't have access to a ping, eg. they left the server, then copy their ID either from their account or from the ?playlist contributors <playlistname>")
              await asyncio.sleep(15)
              await message.delete()
            else:
              with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "w") as b:
                new_data = json.dumps(data, indent=4)
                b.write(new_data)
                b.close()
                await ctx.send(f"Successfully removed {removal.name} from`{playlist.lower()}`!")
        else:
          message = await ctx.send(f"You don't own `{playlist.lower()}`, are you sure you entered the right name?")
          await asyncio.sleep(15)
          await message.delete()
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()

  @remove_contributor.error
  async def remove_contributor_error(self, ctx, error):
    if isinstance(error, commands.BadArgument):
      message = await ctx.send(f"{error}. Are you mentioning the contributor...?\n```?playlist remove_contributor <playlist name> @TheContributor#0001```")

  @playlist.command()
  async def list_contributor(self, ctx, playlist):
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        if data["contributors"]:
          length = len(data["contributors"])
          for i in range(length):
            if i == 0:
              contributor_data = f"<@{data['contributors'][i]}>"
            else:
              contributor_data += f"\n<@{data['contributors'][i]}>"
          embed = discord.Embed(color = 0xa3be8c)
          embed.add_field(name=f"{playlist} Contributor(s):", value=contributor_data)
          await ctx.send(embed=embed)
        else:
          message = await ctx.send(f"`{playlist.lower()}` doesn't contain any contributors.")
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")
      await asyncio.sleep(15)
      await message.delete()
  
  # Function deletes a playlist if they are a owner
  @playlist.command()
  async def delete(self, ctx, playlist): # delete a playlist
    if path.isfile(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json"):
      with open(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json", "r") as x:
        data = json.load(x)
        if ctx.author.id == data["owner"]:
          delete_confirmation = await ctx.send(f"Please confirm deleting {playlist}.")
          await delete_confirmation.add_reaction("✅")

          def playlist_delete_check(reaction, user):
            return str(reaction) == "✅" and user == ctx.author
          try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=25.0, check=playlist_delete_check)
          except asyncio.TimeoutError:
            await delete_confirmation.delete()
          else:
            await delete_confirmation.delete()
            os.remove(f"{self.SYSTEMPATH}/playlists/{playlist.lower()}.json")
            await ctx.send(f"Successfully deleted `{playlist.lower()}`")
        else:
          message = await ctx.send(f"You don't own `{playlist.lower()}`, are you sure you entered the right name?")
          await asyncio.sleep(15)
          await message.delete()
    else:
      message = await ctx.send(f"`{playlist.lower()}` doesn't exist, are you sure you entered the right name?")

  @playlist.command()
  async def listall(self, ctx):
    playlist_glob = glob.glob(f'{self.SYSTEMPATH}playlists/*.json')
    path = len(f"{self.SYSTEMPATH}/playlists")
    playlist_list = []
    for i in playlist_glob:
      playlist_name = i[path:-5]
      with open(i) as x:
        data = json.load(x)
        owner = data["owner"]
      playlist_entry = f"`{playlist_name}` by <@{owner}>"
      playlist_list.append(playlist_entry)
    playlist_list = sorted(playlist_list, key=str.lower)
    playlist_send = '\n'.join(playlist_list)
    embed = discord.Embed(color = 0xa3be8c)
    embed.add_field(name="Playlists:", value=playlist_send)
    await ctx.send(embed=embed)


# ?play Section:
  # Queue system, uses asyncio.Event() and asyncio.Queue().
  async def play_queue_system(self):
    while True: # While loop
      self.play_next_queue.clear() # Set the flag to false
      task = await self.play_song_queue.get() # Fetch most recent task (this is an array, where the 0th term is the voice_client object, and the second is the path to the video)
      connected = task[0] # Fetch the 1st element
      path = task[1] # Fetch the 2nd element
      await self.play_queue(connected, path) # Throw these into play_queue()
      await self.play_next_queue.wait() # The flag must be True for the next iteration to continue, this flag is set in play_queue()

  # This is the actual task for the queue system, it plays the audio and when the audio is done playing, it sets the play_next_queue flag to true so that the while loop in play_queue_system() can finish
  async def play_queue(self, connected, path):
    await self.audio_share.acquire()
    connected.play(discord.FFmpegPCMAudio(path)) # Play the audio
    playing = connected.is_playing() # define playing (This should always be true if the above happens without an error)
    while playing == True: # While loop, if playing is true, continue
      playing = connected.is_playing() # Redefine playing, when the audio is done playing (it is set to False) the loop will finish
      await asyncio.sleep(0.1)
    if os.path.exists(path):
      os.remove(path)
    self.play_song_queue.task_done() # This tells the queue that the task has finished completely, and that it can be removed from the dictionary
    self.audio_share.release()
    self.play_next_queue.set() # This sets the play_next_queue() to True.

  # Play command, this must have a link
  @commands.has_role(DJ)
  @commands.command()
  async def play(self, ctx, *, search_term):
    if self.play_lock.is_set() == False:
      message = await ctx.send("Sorry, a playlist is either playing or is being queued, run `?playlist stop` to start a vote to stop the playlist.")
      await asyncio.sleep(25)
      await message.delete()
    else:
      if self.is_voice_connected(ctx) == True: # If is_voice_connected() == True then connected = ctx.voice_client
        connected = ctx.voice_client
      else: # Otherwise, please connect
        channel = ctx.author.voice.channel
        connected = await channel.connect()

      # Download the audio
      result = YoutubeSearch(search_term, max_results = 1).to_dict()
      title = result[0]["title"]
      vid_id = result[0]["id"]
      message = await ctx.send(f"Added/playing {title}\nVideo Link: `https://youtu.be/{vid_id}`")
      download = self.download_audio(f"https://youtu.be/{vid_id}")
      await self.play_song_queue.put([connected, download]) # Parse it into the queue

  @play.error
  async def play_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send()
      await asyncio.sleep(5)
      await message.delete()

  # Join the voice channel, but don't play anything
  @commands.has_role(DJ)
  @commands.command()
  async def join(self, ctx):
    if self.play_lock.is_set():
      channel = ctx.author.voice.channel
      connected = await channel.connect()

  @join.error
  async def join_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send()
      await asyncio.sleep(5)
      await message.delete()

  # Leave the voice channel
  @commands.has_role(DJ)
  @commands.command()
  async def leave(self, ctx):
    if self.play_lock.is_set():
     await ctx.voice_client.disconnect()

  @leave.error
  async def leave_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send()
      await asyncio.sleep(5)
      await message.delete()

  # Skip the track
  @commands.has_role(DJ)
  @commands.command()
  async def skip(self, ctx):
    if self.play_lock.is_set() == True:
      if Music.is_voice_connected(self, ctx) == True:
        connected = ctx.voice_client
        connected.stop()
      else:
        ctx.send("The bot isn't even connected the voice channel! C'mon...")
    else:
      message = await ctx.send("Sorry, a playlist is either playing or is being queued, run `?playlist stop` to start a vote to stop the playlist.")
      await asyncio.sleep(15)
      await message.delete()

  @skip.error
  async def skip_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

  @commands.has_role(DJ)
  @commands.command()
  async def clear(self, ctx):
    if self.play_lock.is_set() == True:
      if self.is_voice_connected(ctx) == True:
        connected = ctx.voice_client
        connected.stop()
        for x in range(self.play_song_queue.qsize()):
          connected.stop()
          await self.play_song_queue.get()
          self.play_song_queue.task_done()
        remove_files = glob.glob(f'{self.SYSTEMPATH}audio/*.mp3')
        for x in remove_files:
          os.remove(x)
      else:
        message = await ctx.send("The bot isn't connected, so there isn't anything to clear.")
        await asyncio.sleep(15)
        await message.delete()
    else:
       message = await ctx.send("Sorry, a playlist is either playing or is being queued, run `?playlist stop` to start a vote to stop the playlist.")
       await asyncio.sleep(15)
       await message.delete()

  @clear.error
  async def clear_error(self, ctx, error):
    if isinstance(error, commands.MissingRole):
      message = await ctx.send("Sorry you don't have the DJ Role!")
      await asyncio.sleep(5)
      await message.delete()

def setup(client):
  client.add_cog(Music(client))