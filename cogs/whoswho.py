import json
import os
import asyncio
from dotenv import load_dotenv
import discord
import collections
from discord.ext import commands

class WhoIsWho(commands.Cog):
    load_dotenv("../.env")
    STAFF = int(os.getenv("STAFF_ROLE"))
    def __init__(self, client):
        self.client = client
        self.SYSTEMPATH = os.getenv('SYSTEMPATH')
        self.WHOSWHO = int(os.getenv('WHOSWHO_CHANNEL'))

    @commands.group()
    @commands.has_role(STAFF)
    async def whoswho(self, ctx):
        if ctx.invoked_subcommand is None:
            message = await ctx.send("Invalid whoswho command!")
            await asyncio.sleep(15)
            await message.delete()

    @whoswho.error
    async def whoswho_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            message = await ctx.send("Sorry you don't have the Staff Role!")
            await asyncio.sleep(5)
            await message.delete()

    @whoswho.command()
    async def initialize(self, ctx):
        with open(f"{self.SYSTEMPATH}whoswho.json", "r") as x:
            data = json.load(x)
            if "message_id" in data:
                message = await ctx.send("A whoswho already exists, do you want to recreate this message?")
                await message.add_reaction("✅")

                def whoswho_initialize_check(reaction, user):
                    return str(reaction) == "✅" and user == ctx.author
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=25.0, check=whoswho_initialize_check)
                except asyncio.TimeoutError:
                    await message.delete()
                else:
                    await message.delete()
                    channel = self.client.get_channel(self.WHOSWHO)
                    old_whoswho = await channel.fetch_message(data["message_id"])
                    await old_whoswho.delete()
                    embed = discord.Embed(colour = 0xd4af37)
                    embed.set_author(name="Who is Who")
                    message = await channel.send(embed=embed)
                    data["message_id"] = message.id
                    with open(f"{self.SYSTEMPATH}whoswho.json", "w") as x:
                        json.dump(data, x, indent=4)
                    await ctx.send("Successfully created the new WhosWho")

            else:
                channel = self.client.get_channel(self.WHOSWHO)
                embed = discord.Embed(colour = 0xd4af37)
                embed.set_author(name="Who is Who")
                message = await channel.send(embed=embed)
                data["message_id"] = message.id
                with open(f"{self.SYSTEMPATH}whoswho.json", "w") as x:
                    json.dump(data, x, indent=4)
                await ctx.send("Successfully created the WhosWho")

    @whoswho.command()
    async def reload(self, ctx):
        with open(f"{self.SYSTEMPATH}whoswho.json", "r") as x:
            data = json.load(x)
            if "message_id" in data:
                embed = discord.Embed(colour = 0xd4af37)
                embed.set_author(name="Who is Who")
                for i in data:
                    if i != "message_id":
                        field_data = ""
                        for j in data[i]:
                            field_data += f"<@{j[0]}> - {j[1]} {j[2]}\n"
                        embed.add_field(name=i, value=field_data[:-1], inline=False)

                channel = self.client.get_channel(self.WHOSWHO)
                message = await channel.fetch_message(data["message_id"])
                await message.edit(embed=embed)
            else:
                message = await ctx.send("A whoswho doesn't exist, please run `?whoswho initialize` to reload it.")
                await asyncio.sleep(15)
                await message.delete()

    @whoswho.command()
    async def add(self,  ctx, user: discord.User, *argv):
        with open(f"{self.SYSTEMPATH}whoswho.json", "r") as x:
            data = json.load(x)
            if "message_id" in data:
                if len(argv) != 2: 
                    message = await ctx.send("Please Limit the whoswho additions to First and Last name\n```?whoswho add @TheUser#0001 First_Name Last_Name```")
                    await asyncio.sleep(15)
                    await message.delete()
                else:
                    name_data = [user.id]
                    for arg in argv:
                        name_data.append(arg)

                    last_name_initial = name_data[2][0]
                    with open(f"{self.SYSTEMPATH}whoswho.json", "w") as x:
                        try:
                            if data[last_name_initial]:
                                data[last_name_initial].append(name_data)
                            else:
                                data[last_name_initial] = []
                                data[last_name_initial].append(name_data)
                        except KeyError:
                            data[last_name_initial] = []
                            data[last_name_initial].append(name_data)
                        data = collections.OrderedDict(sorted(data.items()))
                        json.dump(data, x, indent=4)

                    embed = discord.Embed(colour = 0xd4af37)
                    embed.set_author(name="Who is Who")

                    for i in data:
                        if i != "message_id":
                            field_data = ""
                            for j in data[i]:
                                field_data += f"<@{j[0]}> - {j[1]} {j[2]}\n"
                            embed.add_field(name=i, value=field_data[:-1], inline=False)

                    channel = self.client.get_channel(self.WHOSWHO)
                    message = await channel.fetch_message(data["message_id"])
                    await message.edit(embed=embed)
            else: 
                message = await ctx.send("A whoswho doesn't exist, please run `?whoswho initialize` to begin adding/removing people to it.")
                await asyncio.sleep(15)
                await message.delete()

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            message = await ctx.send("Make sure you are pinging the user being added to the whoswho!")
            await asyncio.sleep(15)
            await message.delete()
        else:
            print(error)

    @whoswho.command()
    async def remove(self, ctx, user: discord.User):
        with open(f"{self.SYSTEMPATH}whoswho.json", "r") as x:
            data = json.load(x)
            if "message_id" in data:
                confirmation = False
                for i in data:
                    if i != "message_id":
                        g = -1
                        for j in data[i]:
                            g += 1
                            if j[0] == user.id:
                                confirmation = True
                                del data[i][g]
                if confirmation:
                    for i in list(data):
                        if bool(data[i]) == False:
                            del data[i]
                    embed = discord.Embed(colour = 0xd4af37)
                    embed.set_author(name="Who is Who")
                    for i in data:
                        if i != "message_id":
                            field_data = ""
                            for j in data[i]:
                                field_data += f"<@{j[0]}> - {j[1]} {j[2]}\n"
                            embed.add_field(name=i, value=field_data[:-1], inline=False)
                    channel = self.client.get_channel(self.WHOSWHO)
                    message = await channel.fetch_message(data["message_id"])
                    await message.edit(embed=embed)
                    with open(f"{self.SYSTEMPATH}whoswho.json", "w") as x:
                        json.dump(data, x, indent=4)

                else:
                    message = await ctx.send(f"Couldn't find {user} in the list, did you correctly specify the right user?")
                    await asyncio.sleep(15)
                    await message.delete()

            else:
                message = await ctx.send("A whoswho doesn't exist, please run `?whoswho initialize` to begin adding/removing people to it.")
                await asyncio.sleep(15)
                await message.delete()

def setup(client):
  client.add_cog(WhoIsWho(client))