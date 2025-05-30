# This file uses the Polygon API to fetch all available equity/ETF tickers and find the top 1000 by volume, then export the results to a text file

# Required packages

import aiohttp
import asyncio
import dotenv
import os
import requests

# Import sensitive variables using .env file

dotenv.load_dotenv(".env") if ".env" in os.listdir() else None
polygon_key = os.getenv("POLYGON_API_KEY")

# Parameters

limit = 1000
max_scan_length = 30_000
max_end_length = 1000
types = ["CS", "ETF", "ETN"]
markets = ["stocks"]

# Global variables

base = "https://api.polygon.io"
ticker_symbols = []
last_ticker = "A"
total_results = limit

# Fetch all symbols on Polygon

for i in range(len(types)):
    type_ = types[i]
    print(f"Handling type {type_}")
    while total_results == limit:
        if last_ticker == "A": # https://polygon.io/docs/stocks/get_v3_reference_tickers
            url = f"{base}/v3/reference/tickers?apiKey={polygon_key}&market={markets[0]}&type={type_}&limit={limit}"
        else:
            if "ticker.gt" in url:
                url = url.split("ticker.gt")[0]
            url = f"{url}&ticker.gt={last_ticker}"
        r = requests.get(url = url)
        symbol_details = r.json()
        if not isinstance(symbol_details, dict):
            print(f"Error: symbol_details = {symbol_details}")
            break
        results = symbol_details.get("results",[])
        if not len(results) > 0:
            print(f"Error: results = {results}")
            break
        ticker_symbolsX = [item["ticker"] for item in results if item['type'] in types]
        first_ticker = ticker_symbolsX[0]
        last_ticker = ticker_symbolsX[-1]
        total_results = len(ticker_symbolsX)
        print(f"Retrieved {type_}, {first_ticker}-{last_ticker}, {total_results} results")
        ticker_symbols += ticker_symbolsX
        if len(ticker_symbolsX) < limit:
            if i == len(types) - 1:
                print(f"Finished, found {len(ticker_symbols)} tickers")
            else:
                print("Moving on to next type")
            total_results = 1000
            last_ticker = "A"
            break

# Get volume numbers (ASYNC)

async def fetch_volume(session, ticker):
    url = f"{base}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={polygon_key}"
    try:
        async with session.get(url) as response:
            data = await response.json()
            volume = data.get("ticker", {}).get("prevDay", {}).get("v", 0)
            return ticker, volume
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return ticker, 0

async def get_all_volumes(tickers):
    volume_dict = {}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_volume(session, ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks)
    return dict(results)

# Run the async volume fetching, sort based on volume, then sort A-Z

ticker_symbols = ticker_symbols[:max_scan_length]
print(f"Getting volume numbers for {len(ticker_symbols)} tickers")
volume_dict = asyncio.run(get_all_volumes(ticker_symbols))
volume_dict = dict(sorted(volume_dict.items(), key=lambda x: x[1], reverse=True))
top_tickers = list(volume_dict.keys())[:max_end_length]
print(f"Top tickers (volume): {top_tickers}")
top_tickers = sorted(top_tickers, reverse=False)
print(f"Top tickers (A-Z): {top_tickers}")

# Export results to text file

with open("universe2.txt", "w") as f:
    f.write("\n".join(top_tickers))
print(f"Created new universe with {len(top_tickers)} tickers")

# END