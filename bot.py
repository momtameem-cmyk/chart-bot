import os
import asyncio
import requests
import pandas as pd
import pandas_ta as ta
from telegram import Bot

# إعداد المتغيرات من env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

# قائمة العملات (تم تقسيمها إلى دفعات لتقليل الضغط على API)
coins_batch_1 = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", "LTC", "TRX", "UNI", "LINK", "BCH", "ETC", "FIL", "AAVE", "ALGO", "ATOM", "AVAX", "BUSD", "CAKE", "CRO", "CVC", "DASH", "DOGE", "DOT", "EOS", "ETC", "FIL", "FTM", "GRT", "HBAR", "ICP", "KSM", "LTC", "MATIC", "NEAR", "NEXO", "OMG", "PAXG", "QTUM", "REN", "SAND", "SHIB", "SUSHI", "TWT", "UMA", "UNI", "USDT", "XLM", "XMR", "XRP", "YFI", "ZRX"]
coins_batch_2 = ["AAVE", "ALGO", "ATOM", "AVAX", "BUSD", "CAKE", "CRO", "CVC", "DASH", "DOGE", "DOT", "EOS", "ETC", "FIL", "FTM", "GRT", "HBAR", "ICP", "KSM", "LTC", "MATIC", "NEAR", "NEXO", "OMG", "PAXG", "QTUM", "REN", "SAND", "SHIB", "SUSHI", "TWT", "UMA", "UNI", "USDT", "XLM", "XMR", "XRP", "YFI", "ZRX"]
coins_batch_3 = ["AAVE", "ALGO", "ATOM", "AVAX", "BUSD", "CAKE", "CRO", "CVC", "DASH", "DOGE", "DOT", "EOS", "ETC", "FIL", "FTM", "GRT", "HBAR", "ICP", "KSM", "LTC", "MATIC", "NEAR", "NEXO", "OMG", "PAXG", "QTUM", "REN", "SAND", "SHIB", "SUSHI", "TWT", "UMA", "UNI", "USDT", "XLM", "XMR", "XRP", "YFI", "ZRX"]
coins_batch_4 = ["AAVE", "ALGO", "ATOM", "AVAX", "BUSD", "CAKE", "CRO", "CVC", "DASH", "DOGE", "DOT", "EOS", "ETC", "FIL", "FTM", "GRT", "HBAR", "ICP", "KSM", "LTC", "MATIC", "NEAR", "NEXO", "OMG", "PAXG", "QTUM", "REN", "SAND", "SHIB", "SUSHI", "TWT", "UMA", "UNI", "USDT", "XLM", "XMR", "XRP", "YFI", "ZRX"]
coins_batch_5 = ["AAVE", "ALGO", "ATOM", "AVAX", "BUSD", "CAKE", "CRO", "CVC", "DASH", "DOGE", "DOT", "EOS", "ETC", "FIL", "FTM", "GRT", "HBAR", "ICP", "KSM", "LTC", "MATIC", "NEAR", "NEXO", "OMG", "PAXG", "QTUM", "REN", "SAND", "SHIB", "SUSHI", "TWT", "UMA", "UNI", "USDT", "XLM", "XMR", "XRP", "YFI", "ZRX"]

# لتخزين آخر حالة لإرسال إشعار عند تقاطع جديد فقط
last_cross = {}

# دالة لجلب بيانات الأسعار
def get_coin_data(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbol, "convert": "USD"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if "data" in data and symbol in data["data"]:
        price = data["data"][symbol]["quote"]["USD"]["price"]
        return price
    return None

# دالة لحساب EMA و RSI
def calculate_indicators(prices):
    df = pd.DataFrame(prices, columns=["close"])
    df["ema7"] = ta.ema(df["close"], length=7)
    df["ema25"] = ta.ema(df["close"], length=25)
    df["rsi"] = ta.rsi(df["close"], length=14)
    return df

# إرسال إشعار تليجرام
async def send_alert(symbol, price):
    text = f"📈 {symbol} crossed EMA7 > EMA25 & RSI ≥ 45!\nPrice: ${price:.2f}"
    await bot.send_message(chat_id=CHAT_ID, text=text)

# الدالة الرئيسية
async def main():
    global last_cross
    while True:
        for batch in [coins_batch_1, coins_batch_2, coins_batch_3, coins_batch_4, coins_batch_5]:
            for symbol in batch:
                try:
                    price = get_coin_data(symbol)
                    if price is None:
                        continue

                    # في هذا المثال نفترض آخر 30 سعرًا متوفرة من API
                    # للتجربة يمكن تكرار السعر الحالي عدة مرات
                    prices = [price]*30

                    df = calculate_indicators(prices)
                    latest = df.iloc[-1]

                    crossed = latest["ema7"] > latest["ema25"] and latest["rsi"] >= 45

                    # إرسال إشعار فقط عند تقاطع جديد
                    if crossed and last_cross.get(symbol) != True:
                        await send_alert(symbol, price)
                        last_cross[symbol] = True
                    elif not crossed:
                        last_cross[symbol] = False

                    # لتجنب تجاوز rate limit
                    await asyncio.sleep(1)

                except Exception as e:
                    await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error fetching {symbol}: {e}")
                    continue

            # انتظار دقيقة كاملة قبل التحقق من كل العملات مرة أخرى
            await asyncio.sleep(60)

# تشغيل البوت
if __name__ == "__main__":
    asyncio.run(main())
