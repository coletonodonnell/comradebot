import discord
import datetime
import json
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get

class Starboard(commands.Cog):
  def __init__(self, client):
    self.client = client
    load_dotenv("../.env")
    self.SYSTEMPATH = os.getenv("SYSTEMPATH")
    self.STARCOUNT_MINIMUM = int(os.getenv("STARCOUNT_MINIMUM"))
    self.STARBOARD = int(os.getenv("STARBOARD_CHANNEL"))
    self.ERRORLOG = int(os.getenv("ERROR_CHANNEL"))

  def starlb_cook(self, memberid, number, subtraction = False):
    with open(f'{self.SYSTEMPATH}starlb.json', 'r') as x: # Open starlb.json
      data = json.load(x)
      if memberid in data: # If memberid is in the starlb.json, continue
        with open(f'{self.SYSTEMPATH}starlb.json', 'w') as x: # open starlb to write
            old_starcount = data[memberid]['starcount'] # Take the old star count, by accessing it via data[memberid]['starcount']
            if subtraction:
              new_starcount = old_starcount - number
            else:
              new_starcount = old_starcount + number # Add one star to it
            del data[memberid] # Delete the memberid entry
            data[memberid] = {} # Create it again
            data[memberid]['starcount'] = new_starcount # with the new star count...
            json.dump(data, x, indent=4, ensure_ascii=False, default=str) # Write it.
      if memberid not in data:  # If memberid isn't in the starlb.json, continue
        if subtraction:
          pass
        else:
          with open(f'{self.SYSTEMPATH}starlb.json', 'w') as x:
              data[memberid] = {}
              data[memberid]['starcount'] = number
              json.dump(data, x, indent=4, ensure_ascii=False, default=str)

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    # if the emoji is a star, carry on:
    if payload.emoji.name == "⭐":
      message = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id) # Define the message variable as grabbing the channel and the message id
      reaction = get(message.reactions, emoji=payload.emoji.name) # Define the reaction variable as message.reactions and the emoji name
      messageId = str(payload.message_id) # Cleans up str(payload.message.id) everywhere 
      memberid = str(message.author.id)
      STARCOUNT_PLUS = int(self.STARCOUNT_MINIMUM) + 1
      if reaction.count == self.STARCOUNT_MINIMUM:
        self.starlb_cook(memberid, self.STARCOUNT_MINIMUM)
        with open(f'{self.SYSTEMPATH}starboard.json', 'r') as x: # Open starboard.json in read mode as x
          data = json.load(x) # Load the json as data
          if messageId in data: # If the messageId is in data and has a count of self.STARCOUNT_MINIMUM reactions, do the following
            pass
          if messageId not in data: # If the messageId is not in data and has a count of self.STARCOUNT_MINIMUM reactions, do the following
            # Initialize the embed
            embed = discord.Embed(colour = 0xd4af37)
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
            # Starboard Logic:
            # if the message doesn't have an attachment but has content:
            if bool(reaction.message.attachments) == False and bool(reaction.message.content) == True:
              embed.add_field(name="Content:", value=str(reaction.message.content), inline=False)

            # if the message has an attachment but does not have content:
            elif bool(reaction.message.attachments) == True and bool(reaction.message.content) == False:
              embed.set_image(url=str(reaction.message.attachments[0].url))

            # if it has both:
            else:
              embed.add_field(name="Content:", value=str(reaction.message.content), inline=False)
              embed.set_image(url=str(reaction.message.attachments[0].url))

            # Build the embed
            embed.add_field(name="Channel:", value=f"<#{message.channel.id}>")
            embed.add_field(name="Jump:", value=f"[Click here!]({message.jump_url})")
            embed.set_footer(text=f"{message.id}")
            star_message = f"{reaction.count} :star:"

            # Send the embed
            starboard_message = await self.client.get_channel(self.STARBOARD).send(content=star_message, embed=embed)
            with open(f'{self.SYSTEMPATH}starboard.json', 'w') as x: # opens starboard.json in write mode as x
              data[messageId] = [] # Creates the messageId object
              data[messageId].append({ # Adds the starboard message to the object as a key, access this as data[messageId][0]['starboardid']
                  'starboardid': starboard_message.id
                })
              json.dump(data, x, indent=4, ensure_ascii=False, default=str)
                
      if reaction.count >= STARCOUNT_PLUS:
        with open(f'{self.SYSTEMPATH}starboard.json', 'r') as x: # Open starboard.json in read mode as x
          data = json.load(x) # Load the json as data
          if messageId in data:
            self.starlb_cook(memberid, 1)
            starboard_message_id = data[messageId][0]['starboardid']
            starboard_message = await self.client.get_channel(self.STARBOARD).fetch_message(starboard_message_id)
            new_edit = f"{reaction.count} :star:"
            await starboard_message.edit(content=new_edit)
          if messageId not in data:
            x = datetime.datetime.now()
            current_time = x.strftime('%Y%m%d%H%M')
            ERROR = f"If reaction.count >= {self.STARCOUNT_MINIMUM} AND if messageId not in data, send to errorlog. THIS SHOULD NEVER HAPPEN! Current time is {current_time}"
            await self.client.get_channel(int(self.ERRORLOG)).send(content=ERROR)

  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, payload):
    if payload.emoji.name == "⭐":
      message = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
      reaction = get(message.reactions, emoji=payload.emoji.name)
      messageId = str(payload.message_id)
      memberid = str(message.author.id)
      STARCOUNT_MINUS = self.STARCOUNT_MINIMUM - 1
      with open(f'{self.SYSTEMPATH}starboard.json', 'r') as x:
        data = json.load(x)
        if reaction != None:
          if reaction.count <= STARCOUNT_MINUS:
            if messageId in data: 
              self.starlb_cook(memberid, self.STARCOUNT_MINIMUM, subtraction=True)
              starboard_message_id = data[messageId][0]['starboardid']
              message = await self.client.get_channel(self.STARBOARD).fetch_message(starboard_message_id)
              await message.delete()
              with open(f'{self.SYSTEMPATH}starboard.json', 'w') as x:
                del data[messageId]
                json.dump(data, x, indent=4, ensure_ascii=False, default=str)
          else:
            if messageId in data:
              self.starlb_cook(memberid, 1, subtraction=True)
              starboard_message_id = data[messageId][0]['starboardid']
              starboard_message = await self.client.get_channel(self.STARBOARD).fetch_message(starboard_message_id)
              new_edit = f"{reaction.count} :star:"
              await starboard_message.edit(content=new_edit)
            if messageId not in data:
              current_time = datetime.datetime.strftime('%Y%m%d%H%M%S')
              ERROR = f"If reaction.count >= {self.STARCOUNT_MINIMUM} AND if messageId not in data, send to errorlog. THIS SHOULD NEVER HAPPEN! Current time is {current_time}"
              await self.client.get_channel(int(self.ERRORLOG)).send(content=ERROR)

  @commands.command(brief="Show the Star Leaderboard")
  async def starlb(self, ctx): # The ?starlb command
    with open(f'{self.SYSTEMPATH}starlb.json', 'r') as x: # Open starlb.json
      data = json.load(x) # Load the starlb.json as data
      placeholderdict = {} # Create a placeholder dictionary
      for k,v in data.items(): # for parts k and v in data.items, do the following
          for y,v in v.items(): # for parts y and v in v.items
            placeholderdict[k] = v # add k as equal to this v
          leaderboard_sorted_dict = {k: v for k, v in sorted(placeholderdict.items(), key=lambda item: item[1], reverse=True)} # Sort the leaderboard. 
      embed = discord.Embed(color = 0xa3be8c) # build embed
      formatted_leaderboard_list = [] # Formatted list
      x = 0 # begin counter
      for k,v in leaderboard_sorted_dict.items(): # For k and v in the sorted dict
        x += 1 # add one to the counter each time
        leaderboard_entry = f'{x}. <@{k}>: {v} :star:' # Add an entry
        formatted_leaderboard_list += [leaderboard_entry] # Add this entry to the dictionary
          
      formatted_leaderboard = '\n'.join(formatted_leaderboard_list) # Create this now as a string, where the seperator is a new line
      embed.add_field(name="Star Leaderboard:", value=formatted_leaderboard) # Add the field with the leaderboard
      await ctx.send(embed=embed) # Send it. 

def setup(client):
  client.add_cog(Starboard(client))