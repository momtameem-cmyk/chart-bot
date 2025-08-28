import os
import requests
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Bot
import asyncio

# =========================
# المتغيرات من env
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# جلب أفضل 300 عملة ميم
# =========================
def get_top_meme_coins(limit=300):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"limit": limit, "sort": "market_cap"}
    data = requests.get(url, headers=headers, params=params).json()
    meme_coins = [coin['symbol'] for coin in data['data'] if 'meme' in coin.get('tags',[])]
    return meme_coins

MEME_COINS = get_top_meme_coins()

# =========================
# جلب بيانات الأسعار (مثال على Binance API)
# =========================
def get_ohlcv(symbol, interval='1h', limit=200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=['open_time','open','high','low','close','volume','close_time',
                                     'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume',
                                     'taker_buy_quote_asset_volume','ignore'])
    df['close'] = df['close'].astype(float)
    return df

# =========================
# توليد chart
# =========================
def generate_chart(df, symbol):
    plt.figure(figsize=(10,5))
    plt.plot(df['close'], label='Close Price')
    plt.plot(ta.ema(df['close'], length=50), label='EMA50')
    plt.plot(ta.ema(df['close'], length=200), label='EMA200')
    plt.title(f"{symbol} Price Chart")
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# =========================
# تحقق الشرط
# =========================
async def check_conditions():
    for symbol in MEME_COINS:
        try:
            df = get_ohlcv(symbol)
            ema50 = ta.ema(df['close'], length=50).iloc[-1]
            ema200 = ta.ema(df['close'], length=200).iloc[-1]
            rsi = ta.rsi(df['close'], length=14).iloc[-1]
            price = df['close'].iloc[-1]

            if price > ema200 and price > ema50 and rsi > 40:
                chart = generate_chart(df, symbol)
                await bot.send_photo(chat_id=CHAT_ID, photo=chart,
                                     caption=f"✅ {symbol} met conditions\nPrice: {price:.4f}\nEMA50: {ema50:.4f}\nEMA200: {ema200:.4f}\nRSI: {rsi:.2f}")
            else:
                print(f"Checked {symbol}, conditions not met.")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

# =========================
# Main loop
# =========================
async def main():
    await bot.send_message(chat_id=CHAT_ID, text="🤖 Bot started (300 meme coins + EMA & RSI alerts).")
    while True:
        await check_conditions()
        await asyncio.sleep(3600)  # تحقق كل ساعة

if __name__ == "__main__":
    asyncio.run(main())
