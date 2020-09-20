# comradebot
A self-hosted discord bot designed for small servers with (mostly) close friends. 

## Requirements 
Python: 
- discord.py[voice]
- python-dotenv
- datetime

Misc:
- youtube-dl

OS:
Designed for a Linux based system, though migrating it over to another shouldn't be that hard.

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
