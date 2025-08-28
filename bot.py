import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot

# إعداد المتغيرات من البيئة
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
CMC_API_KEY = os.getenv('CMC_API_KEY')

bot = Bot(token=TELEGRAM_TOKEN)

HEADERS = {'X-CMC_PRO_API_KEY': CMC_API_KEY, 'Accept': 'application/json'}
CMC_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

# جلب أفضل 200 عملة ميم
def get_top_meme_coins():
    params = {'limit': 200, 'sort':'market_cap'}
    response = requests.get(CMC_URL, headers=HEADERS, params=params)
    data = response.json().get('data', [])
    meme_coins = [coin['symbol'] for coin in data if 'meme' in coin.get('tags', [])]
    return meme_coins

MEME_COINS = get_top_meme_coins()
print(f"Loaded {len(MEME_COINS)} meme coins.")

# دالة لجلب بيانات الأسعار (الـ OHLC) لكل عملة
def get_ohlc(symbol, convert='USD', limit=100):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/latest'
    params = {'symbol': symbol, 'convert': convert, 'timeframe':'1d', 'count':limit}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json().get('data', {}).get('quotes', [])
        df = pd.DataFrame([{
            'close': q['quote'][convert]['close'],
            'open': q['quote'][convert]['open'],
            'high': q['quote'][convert]['high'],
            'low': q['quote'][convert]['low']
        } for q in data])
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# دالة لإنشاء الرسم البياني وإرجاعه كصورة
def plot_chart(df, symbol):
    plt.figure(figsize=(10,5))
    plt.plot(df['close'], label='Close')
    plt.plot(df['close'].ta.ema(50), label='EMA50')
    plt.plot(df['close'].ta.ema(200), label='EMA200')
    plt.title(f'{symbol} Price Chart')
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# التحقق من الشروط وإرسال إشعار
for symbol in MEME_COINS:
    df = get_ohlc(symbol)
    if df is None or df.empty:
        continue
    ema50 = df['close'].ta.ema(50).iloc[-1]
    ema200 = df['close'].ta.ema(200).iloc[-1]
    rsi = df['close'].ta.rsi(14).iloc[-1]
    current_price = df['close'].iloc[-1]

    if current_price > ema200 and current_price > ema50 and rsi >= 40:
        chart_img = plot_chart(df, symbol)
        try:
            bot.send_photo(chat_id=CHAT_ID, photo=chart_img, caption=f"✅ {symbol} meets conditions\nPrice: {current_price}\nEMA50: {ema50}\nEMA200: {ema200}\nRSI: {rsi}")
            print(f"Alert sent for {symbol}")
        except Exception as e:
            print(f"Error sending alert for {symbol}: {e}")
    else:
        print(f"Checked {symbol}, conditions not met.")

# إشعار بداية البوت
try:
    bot.send_message(chat_id=CHAT_ID, text=f"🤖 Bot started ({len(MEME_COINS)} meme coins + EMA/RSI alerts + charts).")
except Exception as e:
    print(f"Error sending start message: {e}")
