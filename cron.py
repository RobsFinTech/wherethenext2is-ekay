# This file will ping the bot to respond to a slash command without user input. It should be run periodically.

# Import required packages

import dotenv
from helper import *
import os
import requests
import time
import traceback

# Import sensitive variables using .env file

dotenv.load_dotenv(".env") if ".env" in os.listdir() else None
token = os.getenv("TOKEN","")
server_id = int(os.getenv("SERVER_ID",0))
client_id = os.getenv("CLIENT_ID","")

# Global variables

discord_base = "https://discord.com/api"
patterns_posted = [
    "inside",
    "outside",
    "rev",
    "doubleinside",
    "holygrail",
    "nirvana",
    "po",
]
timeframes_posted = [
    "30-Minute",
    "1-Hour",
    "2-Hour",
    "4-Hour",
    "1-Day",
    "2-Day",
    "4-Day",
    "5-Day",
    "1-Week",
    "2-Week",
    "1-Month",
    "1-Quarter",
    "6-Month",
    "1-Year",
]
timeframe_channel_map = {
    "30-Minute": "30-minute",
    "1-Hour": "hour",
    "2-Hour": "2-hour",
    "4-Hour": "4-huour",
    "1-Day": "day",
    "2-Day": "2-day",
    "4-Day": "4-day",
    #"5-Day": "5-Day",
    "1-Week": "week",
    "2-Week": "2-week",
    "1-Month": "month",
    "1-Quarter": "quarter",
    "6-Month": "6-month",
    "1-Year": "year",
}

# Discord API functions

def get_guilds():
    url = f"{discord_base}/v10/users/@me/guilds"
    headers = {
        "Authorization": f"Bot {token}"
    }
    try:
        r = requests.get(url = url, headers = headers)
        resp = r.json()
    except:
        print(traceback.format_exc())
        resp = {}
    return resp

def get_channels():
    url = f"{discord_base}/v10/guilds/{server_id}/channels"
    headers = {
        "Authorization": f"Bot {token}"
    }
    try:
        r = requests.get(url=url, headers=headers)
        resp = r.json()
    except:
        print(traceback.format_exc())
        resp = {}
    return resp

def get_channel(channel_name="test"):
    channels = get_channels()
    matching_channels = [item for item in channels if item.get("name","") == channel_name]
    if len(matching_channels) > 0:
        channel = matching_channels[0]
    else:
        channel = {}
    if not channel or not isinstance(channel, dict):
        print(f"Error: channels={channels}")
        channel = {}
    return channel

def get_commands():
    guilds = get_guilds()
    if isinstance(guilds, list):
        guild = guilds[0] if len(guilds) > 0 else {}
    else:
        guild = guilds
    if not isinstance(guild, dict):
        print(f"Error: guild={guild}")
        guild = {}
    guild_id = guild.get("id","")
    url = f"{discord_base}/v10/applications/{client_id}/guilds/{guild_id}/commands"
    headers = {"Authorization": f"Bot {token}"}
    try:
        r = requests.get(url = url, headers = headers)
        resp = r.json()
    except:
        print(traceback.format_exc())
        resp = {}
    return resp

def get_command(command_name="signal"):
    commands = get_commands()
    matching_commands = [item for item in commands if item.get("name","") == command_name]
    if len(matching_commands) > 0:
        command = matching_commands[0]
    else:
        command = {}
    if not command or not isinstance(command, dict):
        print(f"Error: commands={commands}")
        command = {}
    return command

def post_command(channel_name="test", command_name="signal", pattern="doji", timeframe="4-Hour"):
    command = get_command(command_name)
    command_id = command.get("id","")
    guild_id = command.get("guild_id","")
    channel = get_channel(channel_name)
    channel_id = channel.get("id","")
    url = f"{discord_base}/v10/interactions"
    data = {
        "type": 2,  # Type 2 means application command
        "application_id": client_id,
        "guild_id": guild_id,
        "channel_id": channel_id,
        "id": command_id,
        "data": {
            "name": command_name,
            "options": [
                {"name": "pattern", "type": 3, "value": pattern},
                {"name": "timeframe", "type": 3, "value": timeframe}
            ]
        }
    }
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url = url, headers = headers, json = data)
        resp = r.json()
    except:
        print(traceback.format_exc())
        resp = {}
    return resp

def post_all_commands():
    channel_name = "test"
    command_name = "signal"
    for pattern in patterns:
        for timeframe in timeframes[:1]:
            print(f"Running command {command_name} in channel {channel_name}: pattern = {pattern}, timeframe = {timeframe}")
            post_command(channel_name, command_name, pattern, timeframe)
            time.sleep(1)
    return patterns

def post_message(channel_name="test", command_name="signal", pattern="doji", timeframe="4-Hour"):
    channel = get_channel(channel_name)
    channel_id = channel.get("id","")
    url = f"{discord_base}/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": f"/{command_name} pattern:{pattern} timeframe:{timeframe}"
    }
    try:
        r = requests.post(url=url, headers=headers, json=data)
        resp = r.json()
    except:
        print(traceback.format_exc())
        resp = {}
    return resp

def post_all_messages(channel_name="test", command_name="signal", patterns_=patterns_posted, timeframes_=timeframes_posted, testing=False):
    time1 = time.time()
    now = dt.datetime.now(tz=market_timezone)
    now_str = now.strftime("%H:%M")
    is_eod = now_str in ["16:00"]
    counter = 0
    for pattern in patterns_posted:
        if pattern not in patterns:
            print(f"Error: pattern={pattern}")
            continue
        for timeframe in timeframes_posted:
            counter += 1
            if timeframe not in timeframes:
                print(f"Error: timeframe={timeframe}, timeframes={timeframes}")
                continue
            if timeframe not in timeframe_channel_map:
                print(f"Error: timeframe={timeframe}, timeframe_channel_map={timeframe_channel_map}")
                continue
            channel_name = timeframe_channel_map.get(timeframe,channel_name)
            if testing:
                channel_name = "test"
                time_conditions = True
            elif timeframe == "30-Minute":
                time_intervals = ["10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00"] # 13 Bars
                time_conditions = is_weekday() and now_str in time_intervals
            elif timeframe == "1-Hour":
                time_intervals = ["10:30","11:30","12:30","13:30","14:30","15:30","16:00"] # 7 Bars
                time_conditions = is_weekday() and now_str in time_intervals
            elif timeframe == "2-Hour":
                time_intervals = ["11:30","13:30","15:30","16:00"] # 4 Bars
                time_conditions = is_weekday() and now_str in time_intervals
            elif timeframe == "4-Hour":
                time_intervals = ["13:30","16:00"] # 2 Bars
                time_conditions = is_weekday() and now_str in time_intervals
            elif timeframe == "1-Day":
                time_conditions = is_weekday() and is_eod
            elif timeframe == "2-Day":
                time_conditions = is_weekday() and is_eod
            elif timeframe == "4-Day":
                time_conditions = is_weekday() and is_eod
            elif timeframe == "5-Day":
                time_conditions = is_weekday() and is_eod
            elif timeframe == "1-Week":
                time_conditions = is_friday() and is_eod
            elif timeframe == "2-Week":
                time_conditions = is_friday() and is_eod
            elif timeframe == "1-Month":
                time_conditions = is_last_trading_day("Month") and is_eod
            elif timeframe == "1-Quarter":
                time_conditions = is_last_trading_day("Quarter") and is_eod
            elif timeframe == "6-Month":
                time_conditions = is_last_trading_day("Half") and is_eod
            elif timeframe == "1-Year":
                time_conditions = is_last_trading_day("Year") and is_eod
            else:
                print(f"Error: timeframe={timeframe}")
                time_conditions = False
            if not time_conditions:
                print(f"Skipping command {command_name} in channel {channel_name}: pattern = {pattern}, timeframe = {timeframe} due to time_conditions = {time_conditions}")
                continue
            print(f"Running command {command_name} in channel {channel_name}: pattern = {pattern}, timeframe = {timeframe}")
            post_message(channel_name, command_name, pattern, timeframe)
            time.sleep(30) # Give the bot time to process the command before sending it another command
    time2 = time.time()
    total_seconds = round(time2 - time1, 2)
    total_minutes = round(total_seconds / 60, 1)
    if total_minutes >= 1:
        print(f"Ran all {counter} /signal combos in {total_minutes} minutes")
    else:
        print(f"Ran all {counter} /signal combos in {total_seconds} seconds")
        now = dt.datetime.now()
        seconds_to_next_minute = 60 - now.second
        print(f"Sleeping {seconds_to_next_minute} seconds to the next minute to prevent duplicate messages")
        time.sleep(seconds_to_next_minute)
    return patterns

# Run the task

post_all_messages()

# END