import os, json, time, yfinance as yf
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

# Setup Clients
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
ALPACA_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY')
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
CHATTING_ID = os.getenv('TELEGRAM_CHAT_ID') # Make sure this is in your .env!

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"

def save_bot_status(equity):
    status_data = {"last_update": datetime.now().strftime("%H:%M:%S"), "equity": float(equity)}
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=4)

def ask_shifu_advice(symbol, price_data):
    prompt = f"Analyze {symbol} data: {price_data}. As Shifu, give a 1-sentence verdict. Should we BUY or WAIT? Use Malaysian wit."
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

def send_trade_advice(symbol, advice):
    markup = InlineKeyboardMarkup()
    
    # Generate buttons for 100, 200, 300... 1000
    buttons = []
    for amount in range(100, 1100, 100):
        buttons.append(InlineKeyboardButton(f"${amount}", callback_data=f"buy_{symbol}_{amount}"))
    
    # Organize buttons into rows of 3
    # This creates:
    # [ $100 ] [ $200 ] [ $300 ]
    # [ $400 ] [ $500 ] [ $600 ] ...
    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])
    
    # Add the Ignore button at the very bottom
    markup.add(InlineKeyboardButton("❌ IGNORE ADVICE", callback_data="ignore"))
    
    msg = f"🦁 *SHIFU TRADING ADVICE: {symbol}*\n\n{advice}"
    bot.send_message(CHATTING_ID, msg, reply_markup=markup, parse_mode='Markdown')

def run_analysis_cycle(symbols):
    print(f"\n--- 🧠 Analysis Start: {datetime.now().strftime('%H:%M:%S')} ---")
    account = trading_client.get_account()
    save_bot_status(account.equity)
    
    for sym in symbols:
        data = yf.download(sym, period="1d", interval="1h", progress=False)
        if not data.empty:
            advice = ask_shifu_advice(sym, data.tail(5).to_string())
            print(f"📡 Sending advice for {sym} to Telegram...")
            send_trade_advice(sym, advice)
        time.sleep(2) # Small gap between messages

if __name__ == "__main__":
    while True:
        try:
            with open(WATCHLIST_FILE, "r") as f:
                watchlist = json.load(f)["symbols"]
            run_analysis_cycle(watchlist)
            time.sleep(3600)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(60)


