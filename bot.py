import os
import asyncio
import pandas as pd
import pandas_ta as ta
import requests
from telegram import Bot

# ==========================
# المتغيرات من ملف env
# ==========================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CMC_API_KEY = os.environ.get("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# ==========================
# قائمة العملات (مثال عام 300 رمز)
# ==========================
COINS = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "DOGE", "AVAX", "MATIC",
    # ضع باقي العملات هنا حتى تصل إلى 300
]

# ==========================
# دالة لجلب الأسعار من CoinMarketCap
# ==========================
def fetch_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    response = requests.get(url, headers=headers)
    data = response.json()
    price = data['data'][symbol]['quote']['USD']['price']
    return price

# ==========================
# دالة حساب المؤشرات
# ==========================
def calculate_indicators(df):
    df['EMA7'] = ta.ema(df['close'], length=7)
    df['EMA25'] = ta.ema(df['close'], length=25)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

# ==========================
# إرسال الإشعار بشكل async
# ==========================
async def send_alert(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)

# ==========================
# فحص العملات وإرسال التنبيهات
# ==========================
async def check_coins():
    for coin in COINS:
        try:
            price = fetch_price(coin)
            # بيانات وهمية للـ dataframe (يمكنك تعديلها للـ API الحقيقية)
            df = pd.DataFrame({'close': [price]*30})
            df = calculate_indicators(df)

            # شرط الإشعار
            if df['EMA7'].iloc[-1] > df['EMA25'].iloc[-1] and df['RSI'].iloc[-1] >= 45:
                await send_alert(f"✅ {coin}: EMA7 > EMA25 و RSI={df['RSI'].iloc[-1]:.2f}")

        except Exception as e:
            await send_alert(f"❌ Error fetching {coin}: {e}")

# ==========================
# حلقة التشغيل المستمرة
# ==========================
async def main():
    await send_alert("🤖 Bot started (300 coins + EMA & RSI alerts).")
    while True:
        await check_coins()
        await asyncio.sleep(60)  # كل دقيقة

if __name__ == "__main__":
    asyncio.run(main())
