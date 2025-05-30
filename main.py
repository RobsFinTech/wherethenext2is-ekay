# Thie file creates the bot as well as its slash commands and runs it

# Import required packages

import discord
from discord.ext import commands
import dotenv
from helper import *
import os
from polygon_ import *
import re
from style import *
import time

# Import sensitive variables using .env file

dotenv.load_dotenv(".env") if ".env" in os.listdir() else None
token = os.getenv("TOKEN","")
server_id = int(os.getenv("SERVER_ID",0))

# Define intents

intents = discord.Intents().default()
intents.guilds = True
intents.message_content = True

# Create filtering function

async def create_embeds(pattern="doji", timeframe="", interval="", timespan="", interaction=None, guild=None):

    # Import the ticker universe

    with open("universe2.txt", "r") as f: # universe2 is the self-updating one, universe is the original one
        tickers = [line.strip() for line in f.readlines()]
    print(f"Found {len(tickers)} tickers in stock universe")
    if not 1000 >= len(tickers) >= 10:
        error_msg = "Error: Stock universe size is either too big or too small"
        print(error_msg)
        return error_msg
    
    # Determine the relevant candle pattern function and the number of candles needed for that particular function

    candles_nbr = pattern_candles_dict.get(pattern,1)
    pattern_func_name = f"is_{pattern}"
    pattern_func = globals().get(pattern_func_name)
    if not pattern_func:
        print(f"Error: Could not find {pattern_func_name} in globals")
        error_msg = f"Error: Invalid pattern {timeframe}"
        return error_msg
    
    # Get all emojis

    if guild:
        emojis = await guild.fetch_emojis()
    elif interaction:
        emojis = interaction.guild.emojis
    else:
        error_msg = "Error: Could not fetch emojis"
        print(error_msg)
        return error_msg

    # Get specific emojis

    red_emote = discord.utils.get(emojis, name="emoji_1")
    green_emote = discord.utils.get(emojis, name="emoji_2")
    #red_hourly = discord.utils.get(emojis, name="red_h")
    #green_hourly = discord.utils.get(emojis, name="green_h")
    red_daily = discord.utils.get(emojis, name="red_d")
    green_daily = discord.utils.get(emojis, name="green_d")
    red_week = discord.utils.get(emojis, name="red_w")
    green_week = discord.utils.get(emojis, name="green_w")
    red_month = discord.utils.get(emojis, name="red_m")
    green_month = discord.utils.get(emojis, name="green_m")
    red_quarter = discord.utils.get(emojis, name="red_q")
    green_quarter = discord.utils.get(emojis, name="green_q")
    #red_year = discord.utils.get(emojis, name="red_y")
    #green_year = discord.utils.get(emojis, name="green_y")

    # Fetch the data

    filtered_tickers = []
    async with aiohttp.ClientSession() as session:
        if pattern in patterns_needing_extra_data:
            data_batches = {}
            for ts in timespans:
                if ts in ["second","minute"]:
                    continue
                ts_interval = interval if ts == timespan else "1"
                data_batches[ts] = await fetch_stock_data_batch(session, tickers, ts_interval, ts, None, None, True, "desc", 5000)
            batch_zip = zip(data_batches["hour"],data_batches["day"],data_batches["week"],data_batches["month"],data_batches["quarter"],data_batches["year"],tickers)
            for hourly_data, daily_data, weekly_data, monthly_data, quarterly_data, yearly_data, tickers in batch_zip:
                hourly_results = hourly_data.get('results',[{}]*candles_nbr)
                if timeframe in ["1-Hour","2-Hour","4-Hour"]:
                    hourly_results = resample_results(hourly_results, new_timeframe=timeframe)
                daily_results = daily_data.get('results',[{}]*candles_nbr)
                if timeframe in ["2-Day","4-Day","5-Day"]:
                    daily_results = resample_results(daily_results, new_timeframe=timeframe)
                weekly_results = weekly_data.get('results',[{}]*candles_nbr)
                if timeframe in ["1-Week","2-Week","3-Week"]:
                    weekly_results = resample_results(weekly_results, new_timeframe=timeframe)
                monthly_results = monthly_data.get('results',[{}]*candles_nbr)
                if timeframe in ["6-Month"]:
                    monthly_results = resample_results(monthly_results, new_timeframe=timeframe)
                quarterly_results = quarterly_data.get('results',[{}]*candles_nbr)
                yearly_results = yearly_data.get('results',[{}]*candles_nbr)
                timespan_results_map = {
                    "hour": hourly_results,
                    "day": daily_results,
                    "week": weekly_results,
                    "month": monthly_results,
                    "quarter": quarterly_results,
                    "year": yearly_results
                }
                #hourly_color = green_hourly if hourly_results[0].get('c',0) > hourly_results[0].get('o',0) else red_hourly
                daily_color = green_daily if daily_results[0].get('c',0) > daily_results[0].get('o',0) else red_daily
                weekly_color = green_week if weekly_results[0].get('c',0) > weekly_results[0].get('o',0) else red_week
                monthly_color = green_month if monthly_results[0].get('c',0) > monthly_results[0].get('o',0) else red_month
                quarterly_color = green_quarter if quarterly_results[0].get('c',0) > quarterly_results[0].get('o',0) else red_quarter
                #yearly_color = green_year if yearly_results[0].get('c',0) > yearly_results[0].get('o',0) else red_year
                results = timespan_results_map.get(timespan)
                if results is None:
                    print(f"Error: results={results}, timespan={timespan}")
                    continue
                # results = sorted(results, key=lambda x: x.get('t',0), reverse=False)
                candles = results[:candles_nbr] # Only pay attention to the number of candles required to determine that particular pattern
                if len(candles) < candles_nbr or candles == [{}] * candles_nbr:
                    print(f"Error: candles={candles}, candles_nbr={candles_nbr}")
                    continue
                if pattern_func(*candles): # Analyze all the candles against the chosen pattern
                    filtered_ticker = f"{daily_color} {weekly_color} {monthly_color} {quarterly_color}   {tickers}"
                    filtered_tickers.append(filtered_ticker)
        else:
            stock_data_responses = await fetch_stock_data_batch(session, tickers, interval, timespan, None, None, True, "desc", 5000)
            for ticker, data in zip(tickers, stock_data_responses):
                if not isinstance(data, dict):
                    print(f"Error: Invalid data type for {ticker}, data={data}")
                    continue
                if "results" not in data:
                    print(f"Error: Invalid data fields for {ticker}, data={data}")
                    continue
                results = data.get("results",[{}]*candles_nbr)
                if not isinstance(results, list):
                    print(f"Error: Invalid results type for {ticker}, results={results}")
                    continue
                if timeframe in timeframes_resampled:
                    # print(f"Resampling results for {timeframe} timeframe")
                    results = resample_results(results, new_timeframe=timeframe)
                # results = sorted(results, key=lambda x: x.get('t',0), reverse=False)
                candles = results[:candles_nbr] # Only pay attention to the number of candles required to determine that particular pattern
                if len(candles) < candles_nbr or candles == [{}] * candles_nbr:
                    print(f"Error: candles={candles}, candles_nbr={candles_nbr}")
                    continue
                if pattern_func(*candles): # Analyze all the candles against the chosen pattern
                    color_dot = str(green_emote) if candles[0].get("c",0) > candles[0].get("o",0) else str(red_emote)
                    filtered_ticker = f"{ticker} {color_dot}"
                    filtered_tickers.append(filtered_ticker)

    # Valid the filtered_tickers

    if not isinstance(filtered_tickers, list):
        error_msg = f"Error: filtered_tickers={filtered_tickers}"
        print(error_msg)
        return error_msg

    # Creates the embeds to post the data in Discord

    pattern = str(pattern).title()
    timeframe = str(timeframe).replace("1-","")
    long_message = '\n'.join(filtered_tickers)
    chunks = split_message(long_message, 4096) # Ensure messages fit Discord's limit
    embeds = []
    if chunks and chunks != ["\n"]:
        for chunk in chunks:
            if chunk.strip():
                embed = discord.Embed(title=f"{pattern} {timeframe} Tickers", description=chunk, color=embed_color)
                embed.set_thumbnail(url=thumbnail_url)
                embed.set_footer(icon_url=footer_url, text=footer_text)
                embeds.append(embed)
    else:
        embed = discord.Embed(title=f"No {pattern} {timeframe} Candles Detected", color=embed_color)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_footer(icon_url=footer_url, text=footer_text)
        embeds.append(embed)

    return embeds

# Add basic bot commands

class Client(commands.Bot): # discord.Client

    async def on_ready(self):
        print(f"Logged on as {self.user}.")
        try:
            # guild = discord.Object(id=server_id)
            guild = self.get_guild(server_id)
            if guild:
                synced = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced)} commands to guild {guild.id}") 
                emojis = await guild.fetch_emojis()
                if emojis:
                    emoji_list = "\n".join(f"{emoji} - `{emoji.name}`" for emoji in emojis)
                    print(f"Here are all the emojis in this server:\n{emoji_list}")
                else:
                    print(f"No custom emojis found for guild {guild.id}")
            else:
                print("Error: Guild not found")
        except Exception as e:
            print(f"Error: {e}")

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
        text = message.content.lower()
        if message.author == self.user: # Don't reply to self unless signal command
            if text.startswith("/signal"):
                try:
                    match = re.search(r'pattern:(\S+)\s+timeframe:(\S+)', text)
                    pattern = match.group(1)
                    timeframe = match.group(2)
                    interval, timespan = str(timeframe).split("-")
                except:
                    error_msg = "Error: Could not parse signal"
                    print(error_msg)
                    await message.channel.send(error_msg)
                    return
                await message.channel.send("Processing... Please wait")
                guild = self.get_guild(server_id)
                embeds = await create_embeds(pattern, timeframe, interval, timespan, None, guild)
                if not isinstance(embeds, list):
                    error_msg = f"Error: embeds={embeds}"
                    print(error_msg)
                    await message.channel.send(error_msg)
                    return
                for embed in embeds:
                    await message.channel.send(embed=embed)
            else:
                return None
        if text.startswith("hello"):
            await message.channel.send(f"Hello {message.author}")

# Create bot

client = Client(command_prefix=bot_prefix, intents=intents)
GUILD_ID = discord.Object(id=server_id)

# Server slash commands (1)

@client.tree.command(name='commandlist', description="Show all the available slash commands", guild=GUILD_ID)
async def commandlist(interaction: discord.Interaction): 
    embed = discord.Embed(title="Command List:", description=command_list, color=embed_color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(icon_url=footer_url ,text=footer_text)
    await interaction.response.send_message(embed=embed)      

# Technical slash commands (1)

@client.tree.command(name="signal", description="Find stocks with the selected pattern on the selected timeframe", guild=GUILD_ID)
@discord.app_commands.choices(pattern=pattern_options, timeframe=timeframe_options)
async def signal(interaction: discord.Interaction, pattern: discord.app_commands.Choice[str], timeframe: discord.app_commands.Choice[str]):

    # Send an initial message so the user knows the bot is working

    time1 = time.time()
    await interaction.response.send_message("Processing... Please wait")

    # Validate the input variables just in case

    pattern = pattern.value
    if not validate_pattern(pattern):
        error_msg = f"Error: Invalid pattern {pattern}"
        print(error_msg)
        await interaction.followup.send(error_msg)
        return
    timeframe = timeframe.value
    if not validate_timeframe(timeframe):
        error_msg = f"Error: Invalid timeframe {timeframe}"
        print(error_msg)
        await interaction.followup.send(error_msg)
        return
    interval, timespan = str(timeframe).split("-")
    timespan = str(timespan).lower()

    # Get and post embeds with filtered tickers

    embeds = await create_embeds(pattern, timeframe, interval, timespan, interaction, None)
    if not isinstance(embeds, list):
        error_msg = f"Error: embeds={embeds}"
        print(error_msg)
        await interaction.followup.send(error_msg)
        return
    for embed in embeds:
        await interaction.followup.send(embed=embed)

    # Measure time

    time2 = time.time()
    total_seconds = round(time2 - time1, 2)
    total_minutes = round(total_seconds / 60, 1)
    if total_minutes > 1:
        print(f"Executed command {pattern} on {timeframe} timeframe in {total_minutes} minutes")
    else:
        print(f"Executed command {pattern} on {timeframe} timeframe in {total_seconds} seconds")

# Run bot

client.run(token=token)

# END