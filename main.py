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

# Assign variable for stock name
stock = 'ETHUSDT'

# datetime interval
intv = 5

# datetime interval
interval = str(intv)+'m'

# datetime interval in seconds
ticks = 2 * 60

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

def data_fetcher():
  # fetch the data from binance
  crypto = spot_client.klines(stock, interval, limit=308)

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

  # Make columns on ema & ma Interactions
  df['gap'] = df['ema'] - df['ma']

  #Convert calc columns into absolute numbers
  df['gap'] = df['gap'].abs()

  # Make Parabolic SAR indicator columns
  df['sar'] = ta.SAR(df['high'], df['low'], acceleration=0.02, maximum=0.2)

  # Remove the first 20 columns with no ema, ma, & calc
  df = df.iloc[20:]

  return df

while True:
  # fetch the data from binance
  data = data_fetcher()

  # Variable for close, ema, ma, sar for 1st value from last
  val_1= data.iloc[-1]
  close_1 = val_1['close']
  ema_1 = val_1['ema']
  ma_1 = val_1['ma']
  sar_1 = val_1['sar']

  # Variable for close, ema, ma, sar for 2st value from last
  val_2= data.iloc[-2]
  close_2 = val_2['close']
  ema_2 = val_2['ema']
  ma_2 = val_2['ma']
  sar_2 = val_2['sar']

  # Variable for close, ema, ma, sar for 3st value from last
  val_3= data.iloc[-3]
  close_3 = val_3['close']
  ema_3 = val_3['ema']
  ma_3 = val_3['ma']
  sar_3 = val_3['sar']

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
  buy = 'Buy ' + stock + ' before ' + last_time + ' | last price $' + last_price
  
  # Sell name template
  sell = 'Sell ' + stock + ' before ' + last_time + ' | last price $' + last_price

  # Buy function 1
  def buy1():
      if (sar_3 > ma_3 > ema_3 and
          sar_2 > ma_2 > ema_2 and
          close_1 > ema_1 > ma_1 > sar_1 and
          (((close_1 - sar_1)/close_1)*100) > 0.3):
          return True
      else:
          return False

  # Buy function 2
  def buy2():
      if ( ema_3 < ma_3 < sar_3 and
          ema_2 < ma_2 < sar_2 and
          sar_1 < ema_1 < close_1 and
          (((abs(sar_1 - close_1))/sar_1)*100) > 0.3):
          return True
      else:
          return False
      
  # Sell function 1
  def sell1():
      if (sar_3 > ema_3 > ma_3 and
          sar_2 > ema_2 > ma_2 and
          sar_1 > ma_1 > ema_1 > close_1 and
          (((sar_1 - close_1)/sar_1)*100) > 0.3):
          return True
      else:
          return False
        
  # Sell function 1
  def sell2():
      if (close_3 > ema_3  > sar_3 > ma_3 and
          close_2 > ema_2 > sar_2 > ma_2  and
          sar_1 > ema_1 > ma_1 and
          sar_1 > open_1 > close_1 and
          (((sar_1 - close_1)/sar_1)*100) > 0.3):
          return True
      else:
          return False

  if buy1() == True:
    telegram_send(buy),
    print('Buy signal 1| Waiting'),
    countdown(300)
  elif sell1() == True:
    telegram_send(sell),
    print('Sell signal 1 | Waiting'),
    countdown(300)
  elif buy2() == True:
    telegram_send(buy),
    print('Buy signal 2 | Waiting'),
    countdown(300)
  elif sell2() == True:
    telegram_send(sell),
    print('Sell signal 2 | Waiting'),
    countdown(300)   
  else:
    print('Waiting'),
    countdown(60)