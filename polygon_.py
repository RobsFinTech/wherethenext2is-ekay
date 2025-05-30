# This file defines functions for linking to the Polygon market data API

# Import required packages

import aiohttp
import asyncio
import datetime as dt
import dotenv
from helper import *
import os
from polygon import RESTClient
from style import *

# Import sensitive variables using .env file

dotenv.load_dotenv(".env") if ".env" in os.listdir() else None
polygon_key = os.getenv("POLYGON_API_KEY")

# Create client

poly = RESTClient(api_key=polygon_key)
base = "https://api.polygon.io/v2"

# Validation functions

def validate_interval(interval=1):
    return interval in intervals

def validate_pattern(pattern="doji"):
    pattern = str(pattern).lower().strip()
    return pattern in patterns

def validate_ticker(ticker="MSFT"):
    ticker = str(ticker).upper().strip()
    try:
        details = poly.get_ticker_details(ticker=ticker)
        return ticker
    except:
        return False
    
def validate_timeframe(timeframe="1-Day"):
    return timeframe in timeframes
    
def validate_timespan(timespan="minute"):
    timespan = str(timespan).lower().strip()
    if timespan in timespans:
        return timespan
    else:
        return False
    
# Fetch stock data
    
async def fetch_stock_data(session=None, ticker="MSFT", multiplier=1, timespan="day", from_date=None, to_date=None, adjusted=True, sort="desc", limit=5000):
    if session is None:
        session = aiohttp.ClientSession()
    now = dt.datetime.now()
    if from_date is None:
        jan_1st = dt.datetime(now.year, 1, 1)
        jan_1st_1 = dt.datetime(now.year - 1, 1, 1)
        first_monday = jan_1st + dt.timedelta(days=(7 - jan_1st.weekday()) % 7)
        if timespan == "minute": # 30-Minute
            from_date = now - dt.timedelta(days=2)
            multiplier = 30
        elif timespan == "hour":
            if now.weekday() in [0, 1]:  # Monday, Tuesday
                from_date = now - dt.timedelta(days=6)
            elif now.weekday() in [2, 3, 4]:  # Wednesday, Thursday, Friday
                from_date = now - dt.timedelta(days=2)
            elif now.weekday() in [5, 6]: # Saturday, Sunday
                from_date = now - dt.timedelta(days=4)
            else:
                from_date = now - dt.timedelta(days=1)
            from_date = from_date.replace(minute=0)
            multiplier = 30
            timespan = "minute"
        elif timespan == "day":
            days_ago = now - dt.timedelta(days=30) # 5-Day
            from_date = min(jan_1st, days_ago)
            multiplier = 1
        elif timespan == "week":
            days_ago = now - dt.timedelta(days=90) # 3-Week
            from_date = min(first_monday, days_ago)
            multiplier = 1
            timespan = "day"
        elif timespan == "month":
            days_ago = now - dt.timedelta(days=365*3)
            from_date = max(jan_1st_1, days_ago)
            multiplier = 1
        elif timespan == "quarter":
            from_date = now - dt.timedelta(days=365)
        elif timespan == "year":
            from_date = now - dt.timedelta(days=365*3)
        else:
            from_date = now - dt.timedelta(days=30)
        if not isinstance(from_date, int):
            from_date = int(from_date.timestamp() * 1000)
        # if not isinstance(from_date, str):
        #     from_date = from_date.strftime("%Y-%m-%d")
    if to_date is None:
        to_date = int(now.timestamp() * 1000)
        # to_date = now.strftime("%Y-%m-%d")
    ticker = str(ticker).upper()
    timespan = str(timespan).lower()
    sort = str(sort).lower()
    url = f'{base}/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted={str(adjusted).lower()}&sort={sort}&limit={limit}&apiKey={polygon_key}'
    # print(f"url={url}")
    async with session.get(url) as response:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            error_text = await response.text()
            print(f"Unexpected content type: {content_type}, Response: {error_text}")
            return None
        try:
            return await response.json()
        except aiohttp.client_exceptions.ContentTypeError:
            print(f"Failed to parse JSON response from {url}")
            return None
    
# https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to

async def fetch_stock_data_batch(session=None, tickers=[], multiplier=1, timespan="day", from_date=None, to_date=None, adjusted=True, sort="asc", limit=5000):
    tasks = [fetch_stock_data(session, ticker, multiplier, timespan, from_date, to_date, adjusted, sort, limit) for ticker in tickers]
    return await asyncio.gather(*tasks)

def show_datetimes():
    for i in range(len(timeframes)):
        timeframe = timeframes[i]
        interval, timespan = timeframe.split("-")
        interval = int(interval)
        timespan = str(timespan).lower()
        data = asyncio.run(fetch_stock_data(multiplier=interval, timespan=timespan))
        results = data.get("results",[])
        if timeframe in timeframes_resampled:
            print(f"Resampling results for {timeframe} timeframe")
            results = resample_results(results, new_timeframe=timeframe)
        times = [pd.to_datetime(item.get("t",0), unit="ms").strftime("%Y-%m-%d %X") for item in results]
        print(f"Default datetimes for timeframe {timeframe}:")
        print(times)

# END