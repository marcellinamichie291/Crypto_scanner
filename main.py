# Import OS
import os

# Common
import pandas as pd
import pytz
import time

# Data Fetcher
from binance.spot import Spot as client

# Import Request
import requests

# Technical Analysis
import talib as ta

# define the countdown func.
def countdown(t):    
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1

# Telegram API Key
my_secret = os.environ['telegram_api']
my_secret1 = os.environ['telegram_chat_id']
api_key = str(my_secret)
chat_id = str(my_secret1)

# Function for Telegram Notification
def telegram_send(chat):
  bot_token = api_key
  bot_chat_id = chat_id
  chat_message = 'https://api.telegram.org./bot' + bot_token + '/sendMessage?chat_id=' + bot_chat_id +'&text=' + chat
  response = requests.get(chat_message)
  return response.json()

# Binance URL api
base_url = 'https://api.binance.com'
spot_client = client(base_url = base_url)

def stock_list():
  pairs = spot_client.exchange_info()
  df = pd.DataFrame(pairs['symbols'])
  df = df[['symbol','permissions']]
  df = df[df['symbol'].str.contains('USDT')]
  selection = ['MARGIN']
  mask = df['permissions'].apply(lambda x: any(item for item in selection if item in x))
  df1 = df[mask]
  s_list =  list(df1["symbol"])
  s_list = [x for x in s_list if x[-4:] == 'USDT']
  return s_list

# Assign variable for stock name
stock = stock_list()

# datetime interval
intv = 5

# datetime interval
interval = str(intv)+'m'

# datetime interval in seconds
ticks = 2 * 60

def data_fetcher(stock_name):
  # fetch the data from binance
  crypto = spot_client.klines(stock_name, interval, limit=308)

  # Make columns names
  columns =['datetime','open','high','low','close','volume', 'close time', 'quote asset volume', 'number of trade', 'taker buy base', 'taker but', 'ignore']

  # Convert the data into dataframe
  df = pd.DataFrame(crypto, columns=columns)

  # Convert datetime columns as datetime type
  df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')

  # Convert OHLC columns into float
  df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)

  # set datetime column as index
  df= df.set_index('datetime')

  # Convert Timezones
  df = df.tz_localize(pytz.timezone('UTC'))
  df.index = df.index.tz_convert('Asia/Jakarta')

  # Reset dataframe index
  df = df.reset_index()

  # Remove the timezone stamp
  df['datetime'] = df['datetime'].dt.tz_localize(None)

  #Drop unnecessary columns
  df = df.drop(['volume', 'close time', 'quote asset volume', 'number of trade', 'taker buy base', 'taker but', 'ignore'], axis=1)

  # set datetime column as index
  df= df.set_index('datetime')

  # Make ema indicator columns
  df['ema'] = ta.EMA(df['close'], 9)

  # Make ma indicator columns
  df['ma'] = ta.MA(df['close'], 20)

  # Make Parabolic SAR indicator columns
  df['sar'] = ta.SAR(df['high'], df['low'], acceleration=0.02, maximum=0.2)

  # Remove the first 20 columns with no ema, ma, & calc
  df = df.iloc[20:]

  return df

while True:
  for x in stock:
    # Varible for the stock name 
    symbol = x
    
    # fetch the data from binance
    data = data_fetcher(symbol)

    # Variable for close, ema, ma, sar for 1st value from last
    val_1= data.iloc[-1]
    close_1 = val_1['close']
    open_1 = val_1['open']
    ema_1 = val_1['ema']
    ma_1 = val_1['ma']
    sar_1 = val_1['sar']

    # Variable for close, ema, ma, sar for 2st value from last
    val_2= data.iloc[-2]
    close_2 = val_2['close']
    open_2 = val_2['open']
    ema_2 = val_2['ema']
    ma_2 = val_2['ma']
    sar_2 = val_2['sar']

    # Variable for close, ema, ma, sar for 3st value from last
    val_3= data.iloc[-3]
    close_3 = val_3['close']
    open_3 = val_3['open']
    ema_3 = val_3['ema']
    ma_3 = val_3['ma']
    sar_3 = val_3['sar']
    
    q0 = float(data['ma'].quantile([0]))
    q1 = float(data['ma'].quantile([0.25]))
    q2 = float(data['ma'].quantile([0.5]))
    q3 = float(data['ma'].quantile([0.75]))
    q4 = float(data['ma'].quantile([1]))
    data_mean = float(data['ma'].mean())

    # Variable for last price in string
    last_price = str(close_1)

    # Reset dataframe index
    data = data.reset_index()
    
    # Last date from dataframe
    last_date = data['datetime'].max()
    
    # Last Date time Offset
    dtnext = last_date + pd.DateOffset(minutes = intv )
    
    # Last time offset
    last_time = dtnext.strftime("%I:%M %p")
    
    # Buy name template
    buy = 'Buy ' + symbol + ' before ' + last_time + ' | last price $' + last_price
    
    # Sell name template
    sell = 'Sell ' + symbol + ' before ' + last_time + ' | last price $' + last_price

    # Buy function 1
    def buy1():
        if (ma_3 > ema_3 > sar_3 and
          ma_2 > ema_2 > sar_2 and
          close_1 > ema_1 > ma_1 > sar_1 and
          (((close_1 - sar_1)/close_1)*100) > 0.5):
            return True
        else:
            return False

    # Buy function 2
    def buy2():
        if (sar_3 > ema_3 and
          sar_2 > ema_2 and
          ema_1 > sar_1 and
          (((close_1 - sar_1)/close_1)*100) > 0.75):
            return True
        else:
            return False
    
    # Buy confrim function
    def buy_confirm():
        if (ma_1 <= (q4 + (q4 * 0.1)) and ma_1 >= q4 or
          ma_1 <= (q3 + (q3 * 0.1)) and ma_1 >= q3 or
          ma_1 <= (q1 + (q1 * 0.1)) and ma_1 >= q1 or
          ma_1 <= (q0 + (q0 * 0.1)) and ma_1 >= q0):
            return True

    # Sell function 1
    def sell1():
        if (sar_3 > ema_3 > ma_3 and
          sar_2 > ema_2 > ma_2 and
          sar_1 > ma_1 > ema_1 > close_1 and
          (((sar_1 - close_1)/sar_1)*100) > 0.5):
            return True
        else:
            return False

    # Sell function 2
    def sell2():
        if (ema_3 > sar_3 and
          ema_2 > sar_2 and
          sar_1 > ema_1 and
          (((sar_1 - close_1)/sar_1)*100) > 0.75):
            return True
        else:
            return False
        
    # Sell Confirm Functions      
    def sell_confirm():
        if (ma_1 >= (q4 - (q4 * 0.1)) and ma_1 <= q4 or
        ma_1 >= (q3 - (q3 * 0.1)) and ma_1 <= q3 or
        ma_1 >= (q1 - (q1 * 0.1)) and ma_1 <= q1 or
        ma_1 >= (q0 - (q0 * 0.1)) and ma_1 <= q0):
            return True

    if buy1() == True:
      print('Buy signal 1| Waiting'),
      countdown(150)
      buy_df = data_fetcher(symbol)
      if buy_df['ema'].iloc[-1] > ema_1 and buy_confirm == True:
        telegram_send('{} Potential Up Trend'.format(symbol))
      else:
        telegram_send('{} Potential False Alarm'.format(symbol))
    elif buy2() == True:
      print('Buy signal 2| Waiting'),
      countdown(150)
      buy_df = data_fetcher(symbol)
      if buy_df['ema'].iloc[-1] > ema_1 and buy_confirm == True:
        telegram_send('{} Potential Up Trend'.format(symbol))
      else:
        telegram_send('{} Potential False Alarm'.format(symbol))
    elif sell1() == True:
      print('Sell signal 1 | Waiting'),
      countdown(150)
      sell_df = data_fetcher(symbol)
      if sell_df['ema'].iloc[-1] < ema_1 and sell_confirm == True:
        telegram_send('{} Potential Down Trend'.format(symbol))
      else:
        telegram_send('{} Potential False Alarm'.format(symbol))
    elif sell2() == True:
      print('Sell signal 2 | Waiting'),
      countdown(150)
      sell_df = data_fetcher(symbol)
      if sell_df['ema'].iloc[-1] < ema_1 and sell_confirm == True:
        telegram_send('{} Potential Down Trend'.format(symbol))
      else:
        telegram_send('{} Potential False Alarm'.format(symbol))
    else:
      print('Scanning {} is done'.format(symbol))