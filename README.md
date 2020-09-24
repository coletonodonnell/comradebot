# comradebot
A self-hosted discord bot designed for small servers with (mostly) close friends. 

## Requirements 
Python: 
- discord.py[voice]
- python-dotenv
- datetime
- youtube_search

Misc:
- youtube-dl
- ffmpeg

OS:
Designed to be hosted a Linux based system, though migrating it over to another shouldn't be that hard.

## Install
0. You will [need to create a bot for this to work](https://discord.com/developers/applications). This **does not have moderation, the idea is that the bot is for small friend groups where that isn't required.**
1. Clone the repository and cd into it.
2. Install the requirements: 
```
pip install -r requirements.txt
```
3. Create a `.env` file inside of the comradebot folder (the same folder that contains `main.py` with the following details: 
```
# .env
DISCORD_TOKEN = ""
DISCORD_GUILD = ""
STARBOARD_CHANNEL = ""
ERROR_CHANNEL = ""
STAFF_ROLE = ""
DJ_ROLE = ""
SYSTEMPATH = ""
STARCOUNT_MINIMUM = ""
```

You will have to fill in the details yourself, inside of the quotation marks. For Channels, the Guild, and roles, those are all the IDs. You will place them inside the quotation marks. The starcount minimum is for the starboard, and it is the minimum number of stars needed to get on the board. The systempath must be an absolute path from the root to the folder main.py is located in, eg. `/home/user/stuff/comradebot/`. **This must have a / at the end.** This is all you have to do. You can create a simple systemd file here to run the bot automatically: 
```
[Unit]
Description=Starts Discord Bot
After=multi-user.target

[Service]
Type=simple
User=admin
ExecStart=/usr/bin/python /path/to/bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Warning:
This bot isn't designed for a large server, in fact scaled high enough some functions could break. I am currently working on fail safes and such so that it can scale up further, but in the meantime, this is designed for servers with 25-50 people max. I haven't tested it with anymore than that.

## Features:
- Starboard
- Music with Playlists and voting Feature
- More to come

## Commands:
### General:
```
?ping
    Ping the bot.

?roll <number>
    Roll  a number between 1 and the selected number. 
    
?starlb
    Display the starboard leaderboard.
```

### Music:
```
Normal:
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
    None of these commands work while a playlist is active.

Playlists:
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
    List every playlist in the guild.
```
