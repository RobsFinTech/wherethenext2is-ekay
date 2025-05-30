# This file define several helper functions used elsewhere in the repository

# Import required packages

import datetime as dt
import discord
import pandas as pd
import pandas_market_calendars as mcal
import pytz
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Helper variables

bot_prefix = "!"
command_list = f"""
    Bot prefix is = {bot_prefix}

    Below is a list of commands that the bot will respond to:

        commandlist
        signal
"""
footer_text = f"© {dt.datetime.now().year},  Let's Get Richer #LGR | Not a Financial Advisor"
footer_url = "https://img-v2-prod.whop.com/FER1H5W8atWEgYliMZwkoyn-Zaj-f7i0S2fkyz8hN44/rs:fit:1280:720/el:1/dpr:2/aHR0cHM6Ly9hc3NldHMud2hvcC5jb20vdXBsb2Fkcy8yMDI0LTAxLTIwL3VzZXJfNzE5MzYwXzY3NDUyODcwLTliMzktNDkyOC1hNWRlLTgyY2MzODg4YmUwOS5qcGVn"
intervals = [1,2,3,4,5,6,7,8,9,10,11,12,195]
interval_options = [discord.app_commands.Choice(name=item, value=item) for item in intervals]
market_timezone = pytz.timezone("US/Eastern")
pattern_candles_dict = {
    "doji": 1,
    "doubleinside": 3,
    # "FTFCinside": 3,
    "gapper": 2,
    "hammer": 1,
    "holygrail": 3,
    "inrev": 3,
    "inside": 2,
    "momohammer": 1,
    "nirvana": 3,
    "outrev": 3,
    "outside": 2,
    "po": 2,
    "rev": 2,
    "shooter": 1,
}
patterns = list(pattern_candles_dict.keys())
patterns_needing_extra_data = [
    "inside",
    "po",
]
pattern_options = [discord.app_commands.Choice(name=item, value=item) for item in patterns]
thumbnail_url = "https://img-v2-prod.whop.com/FER1H5W8atWEgYliMZwkoyn-Zaj-f7i0S2fkyz8hN44/rs:fit:1280:720/el:1/dpr:2/aHR0cHM6Ly9hc3NldHMud2hvcC5jb20vdXBsb2Fkcy8yMDI0LTAxLTIwL3VzZXJfNzE5MzYwXzY3NDUyODcwLTliMzktNDkyOC1hNWRlLTgyY2MzODg4YmUwOS5qcGVn"
timeframes = [
    "30-Minute", # 2025-04-27: New addition
    "1-Hour", # 2025-04-22: New addition
    "2-Hour", # 2025-04-22: New addition
    "4-Hour",
    "1-Day",
    "2-Day",
    "4-Day", # 2025-04-22: New addition
    "5-Day", # 2025-05-05: New addition
    "1-Week",
    "2-Week",
    "3-Week",
    "1-Month",
    "1-Quarter",
    "6-Month",
    "1-Year",
]
timeframe_options = [discord.app_commands.Choice(name=item[2:] if item.startswith("1-") else item, value=item) for item in timeframes]
timeframes_resampled = [
    "30-Minute",
    "1-Hour",
    "2-Hour",
    "4-Hour",
    "2-Day",
    "4-Day",
    "5-Day",
    "1-Week",
    "2-Week",
    "3-Week",
    "6-Month"
]
timespans = [
    # "second",
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "quarter",
    "year"
]
timespan_options = [discord.app_commands.Choice(name=item, value=item) for item in timespans]
utc_timezone = pytz.timezone("UTC")

# Helper functions

def split_message(message, limit):
    lines = message.split('\n')
    messages = []
    current_message = ''
    for line in lines:
        if len(current_message) + len(line) <= limit:
            current_message += line + '\n'
        else:
            messages.append(current_message)
            current_message = line + '\n'
    if current_message:
        messages.append(current_message)
    return messages

def resample_results(results=[], new_timeframe="4-Hour"):
    if not results:
        results = [
            {
                "c": 75.0875,
                "h": 75.15,
                "l": 73.7975,
                "n": 1,
                "o": 74.06,
                "t": 1577941200000,
                "v": 135647456,
                "vw": 74.6099
            }
        ]
    df = pd.DataFrame(data=results)
    cols = list(df.columns)
    if 't' in cols:
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
    else:
        print(f"Error: Column 't' not found in DataFrame columns: {cols}, could not convert to {new_timeframe} timeframe")
        df['timestamp'] = pd.NaT
        return results
    df = df.set_index('timestamp').sort_index()
    agg_dict = {
        't': 'first',
        'o': 'first',
        'h': 'max',
        'l': 'min',
        'c': 'last',
        'v': 'sum',
        'n': 'first',
        'vw': 'last',
    }
    if "Minute" in new_timeframe:
        df2 = df.tz_localize(tz=utc_timezone).tz_convert(tz=market_timezone)
        df2 = df2.between_time('09:30','16:00') # Ignore extended hours data
        new_df = pd.DataFrame(columns=df2.columns) # No actual resampling needed, just filter out unwanted pre/post market data
    elif "Hour" in new_timeframe:
        df2 = df.tz_localize(tz=utc_timezone).tz_convert(tz=market_timezone)
        df2 = df2.between_time('09:30','16:00') # Ignore extended hours data
        new_df = pd.DataFrame(columns=df2.columns) 
        for date, group in df2.groupby(df2.index.date):
            if group.index[0].weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                continue
            if not group.empty:
                date_str = date.strftime('%Y-%m-%d')
                if new_timeframe == "1-Hour":
                    time_intervals = [
                        (pd.Timestamp(f'{date_str} 09:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 10:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 10:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 11:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 11:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 12:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 12:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 14:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 14:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 15:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 15:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 16:00:00', tz=market_timezone))
                    ]
                elif new_timeframe == "2-Hour":
                    time_intervals = [
                        (pd.Timestamp(f'{date_str} 09:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 11:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 11:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 16:00:00', tz=market_timezone))
                    ]
                elif new_timeframe == "4-Hour":
                    time_intervals = [
                        (pd.Timestamp(f'{date_str} 09:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone)),
                        (pd.Timestamp(f'{date_str} 13:30:00', tz=market_timezone), 
                        pd.Timestamp(f'{date_str} 16:00:00', tz=market_timezone))
                    ]
                else:
                    print(f"Error: Unsupported timeframe {new_timeframe}")
                for start_time, end_time in time_intervals:
                    interval_data = group[(group.index >= start_time) & (group.index < end_time)]
                    if not interval_data.empty:
                        interval_row = pd.Series(index=df2.columns)
                        interval_row['o'] = interval_data['o'].iloc[0]
                        interval_row['h'] = interval_data['h'].max()
                        interval_row['l'] = interval_data['l'].min()
                        interval_row['c'] = interval_data['c'].iloc[-1]
                        interval_row['v'] = interval_data['v'].sum()
                        interval_row['n'] = interval_data['n'].sum()
                        interval_row['vw'] = interval_data['vw'].iloc[-1]
                        interval_row['t'] = interval_data['t'].iloc[0]
                        interval_df = pd.DataFrame([interval_row], index=[start_time])
                        if not interval_df.empty and not interval_df.isna().all(axis=None):
                            new_df = pd.concat([new_df, interval_df])
        df2 = new_df.sort_index(ascending=False)
    elif new_timeframe in ["1-Week","2-Week","3-Week","6-Month"]:
        if new_timeframe == "1-Week":
            resample_period = '7D'
        elif new_timeframe == "2-Week":
            resample_period = '14D'
        elif new_timeframe == "3-Week":
            resample_period = '21D'
        elif new_timeframe == "6-Month":
            resample_period = '6MS'
        df2 = df.resample(resample_period, closed='right', label='right').agg(agg_dict).dropna()
        df2 = df2.sort_index(ascending=False)
    elif new_timeframe in ["2-Day","4-Day","5-Day"]:
        df['date'] = df.index.date
        if new_timeframe == "2-Day":
            resample_freq = 2 # trading days
        elif new_timeframe == "4-Day":
            resample_freq = 4
        elif new_timeframe == "5-Day":
            resample_freq = 5
        else:
            resample_freq = 1
            print(f"Error: Unsupported timeframe {new_timeframe}")
        df['group'] = (df['date'].rank(method='first') - 1) // resample_freq
        last_group_num = df['group'].max()
        new_df = pd.DataFrame(columns=df.columns)
        for group_num, group in df.groupby('group'):
            if not group.empty:
                period_start = group.index[0].normalize()
                period_row = pd.Series(index=df.columns)
                period_row['o'] = group['o'].iloc[0]
                period_row['h'] = group['h'].max()
                period_row['l'] = group['l'].min()
                period_row['c'] = group['c'].iloc[-1]
                period_row['v'] = group['v'].sum()
                period_row['n'] = group['n'].sum() if 'n' in group.columns else len(group)
                period_row['vw'] = group['vw'].iloc[-1] if 'vw' in group.columns else None
                period_row['t'] = group['t'].iloc[0]
                period_row = period_row.drop(['group', 'date'])
                period_df = pd.DataFrame([period_row], index=[period_start])
                if group_num == last_group_num or (not period_df.empty and not period_df.isna().all(axis=None)):
                    new_df = pd.concat([new_df, period_df])   
        df2 = new_df.sort_index(ascending=False)
    else:
        df2 = df
        print(f"Error: Unsupported timeframe {new_timeframe}")
    new_results = df2.to_dict(orient="records")
    return new_results

# Candle pattern functions

def is_doji(candle_1):
    high_low_range = candle_1['h'] - candle_1['l']
    if high_low_range == 0:
        return False
    return abs(candle_1['c'] - candle_1['o']) / high_low_range < 0.1

def is_doubleinside(candle_1, candle_2, candle_3):
     return (candle_1['h'] < candle_2['h'] and
             candle_1['l'] > candle_2['l'] and
             candle_2['h'] < candle_3['h'] and
             candle_2['l'] > candle_3['l'])

def is_gapper(candle_1, candle_2):
    return (candle_1['o'] > candle_2['h']) or (candle_1['o'] < candle_2['l'])

def is_hammer(candle_1):
    body = abs(candle_1['o'] - candle_1['c'])
    upper_shadow = candle_1['h'] - max(candle_1['o'], candle_1['c'])
    lower_shadow = min(candle_1['o'], candle_1['c']) - candle_1['l']
    return lower_shadow >= 2 * body and upper_shadow <= 3 * body

def is_holygrail(candle_1, candle_2, candle_3):
     return (candle_1['h'] < candle_2['h'] and
             candle_1['l'] > candle_2['l'] and
             candle_2['h'] > candle_3['h'] and
             candle_2['l'] < candle_3['l'])

def is_holygrail_hybrid(candle_1, candle_2, candle_3):
     return (candle_1['h'] < candle_2['h'] and
             candle_2['l'] > candle_3['l'] and
             candle_2['h'] > candle_3['h'] and
             candle_2['l'] < candle_3['l'])

def is_inrev(candle_1, candle_2, candle_3):
    return (candle_2['h'] < candle_3['h'] and
            candle_2['l'] > candle_3['l'] and
            candle_1['h'] < candle_2['h'] and
            candle_1['l'] < candle_2['l'] and
            candle_1['c'] > candle_1['o']) or (
            candle_2['h'] < candle_3['h'] and
            candle_2['l'] > candle_3['l'] and
            candle_1['h'] > candle_2['h'] and
            candle_1['l'] > candle_2['l'] and
            candle_1['c'] < candle_1['o'])

def is_inside(candle_1, candle_2):
    return (candle_1['h'] < candle_2['h'] and candle_1['l'] > candle_2['l'])

def is_momohammer(candle_1):
    body = abs(candle_1['o'] - candle_1['c'])
    upper_shadow = candle_1['h'] - max(candle_1['o'], candle_1['c'])
    lower_shadow = min(candle_1['o'], candle_1['c']) - candle_1['l']
    return lower_shadow >= 2 * body and upper_shadow <= 0.2 * body

def is_nirvana(candle_1, candle_2, candle_3):
     return (candle_1['h'] > candle_2['h'] and
             candle_1['l'] < candle_2['l'] and
             candle_2['h'] < candle_3['h'] and
             candle_2['l'] > candle_3['l'])

def is_outrev(candle_1, candle_2, candle_3):
    return (candle_2['h'] > candle_3['h'] and
            candle_2['l'] < candle_3['l'] and
            candle_1['h'] > candle_2['h'] and
            candle_1['l'] > candle_2['l'] and
            candle_1['c'] < candle_1['o']) or (
            candle_2['h'] > candle_3['h'] and
            candle_2['l'] < candle_3['l'] and
            candle_1['h'] < candle_2['h'] and
            candle_1['l'] < candle_2['l'] and
            candle_1['c'] > candle_1['o'])

def is_outside(candle_1, candle_2):
    return (candle_1['h'] > candle_2['h'] and
            candle_1['l'] < candle_2['l'])

def is_po(candle_1, candle_2):
    return (candle_1['h'] > candle_2['h'] and candle_1['c'] <= ((candle_2['h'] + candle_2['l']) * 0.5) and candle_1['l'] > candle_2['l']) or \
           (candle_1['l'] < candle_2['l'] and candle_1['c'] >= ((candle_2['h'] + candle_2['l']) * 0.5) and candle_1['h'] < candle_2['h'])

def is_rev(candle_1, candle_2):
    return (
        (candle_1['h'] > candle_2['h'] and
         candle_1['c'] < candle_1['o'] and
         candle_1['l'] > candle_2['l']) or 
        (candle_1['l'] < candle_2['l'] and
         candle_1['c'] > candle_1['o'] and
         candle_1['h'] < candle_2['h'])
    )

def is_shooter(candle_1):
    body = abs(candle_1['c'] - candle_1['o'])
    upper_shadow = candle_1['h'] - max(candle_1['c'], candle_1['o'])
    lower_shadow = min(candle_1['c'], candle_1['o']) - candle_1['l']
    return lower_shadow <= 0.5 * body and upper_shadow >= 2 * body

# Time functions

def get_last_day(interval="Month", year=None, month=None):
    now = dt.datetime.now()
    year = now.year if year is None else year
    month = now.month if month is None else month
    if interval == "Month":
        last_month = month
    elif interval == "Quarter":
        if month in {1, 2, 3}:
            last_month = 3
        elif month in {4, 5, 6}:
            last_month = 6
        elif month in {7, 8, 9}:
            last_month = 9
        else:
            last_month = 12
    elif interval == "Half":
        last_month = 6 if month <= 6 else 12
    elif interval == "Year":
        last_month = 12
    else:
        print(f"Error: Unsupported interval={interval}")
    last_day = dt.date(year, last_month, 1)
    next_month = last_day.month + 1 if last_day.month < 12 else 1
    next_month_year = year if last_day.month < 12 else year + 1
    last_day = dt.date(next_month_year, next_month, 1) - dt.timedelta(days=1)
    return last_day

def get_last_friday(interval="Month", year=None, month=None):
    last_day = get_last_day(interval, year, month)
    while last_day.weekday() != 4:
        last_day -= dt.timedelta(days=1)
    return last_day

def get_last_trading_day(interval="Month", year=None, month=None, exchange="NYSE"):
    exchange = mcal.get_calendar(exchange)
    last_day = get_last_day(interval, year, month)
    first_day = last_day.replace(day=1)
    last_day_str = last_day.strftime("%Y-%m-%d")
    first_day_str = first_day.strftime("%Y-%m-%d")
    schedule = exchange.schedule(start_date=first_day_str, end_date=last_day_str)
    if len(schedule) == 0:
        print(f"Error: schedule={schedule}")
        return last_day
    else:
        last_trading_day = schedule.index[-1]
    return last_trading_day

def is_friday(year=None, month=None, day=None):
    now = dt.datetime.now()
    year = now.year if year is None else year
    month = now.month if month is None else month
    day = now.day if day is None else day
    date = dt.date(year, month, day)
    is_friday_ = date.weekday() == 4
    return is_friday_

def is_last_trading_day(interval="Month", year=None, month=None, day=None):
    if year and month and day:
        now = dt.date(year, month, day)
    else:
        now = dt.datetime.now()
    year = now.year if year is None else year
    month = now.month if month is None else month
    day = now.day if day is None else day
    last_trading_day = get_last_trading_day(interval, year, month)
    now_str = now.strftime("%Y-%m-%d")
    last_str = last_trading_day.strftime("%Y-%m-%d")
    # print(f"now_str={now_str}, last_str={last_str}")
    is_last_trading_day_ = now_str == last_str
    return is_last_trading_day_

def is_weekday(year=None, month=None, day=None):
    now = dt.datetime.now()
    year = now.year if year is None else year
    month = now.month if month is None else month
    day = now.day if day is None else day
    date = dt.date(year, month, day)
    is_weekday_ = date.weekday() < 5 # Monday to Friday (0-4)
    return is_weekday_ 

# END