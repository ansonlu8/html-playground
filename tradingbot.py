import os
import json
import time
import yfinance as yf
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

# Setup Clients
ALPACA_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY')
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

if not ALPACA_KEY or not ALPACA_SECRET:
    print("❌ ERROR: Alpaca keys missing in .env")
    exit()

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"

def save_bot_status(equity):
    """Updates the bridge file so the Chatbot knows our actual balance."""
    status_data = {
        "last_update": datetime.now().strftime("%H:%M:%S"),
        "equity": float(equity),
        "status": "Scanning"
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=4)

def ask_shifu_analysis(symbol, price_data):
    """Sends raw market data to the AI for a technical verdict."""
    prompt = f"Analyze {symbol} market data: {price_data}. As Shifu, give a 1-sentence technical verdict. Entry or stay patient? Use Malaysian wit."
    
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

def run_analysis_cycle(symbols):
    print(f"\n--- 🧠 Shifu Deep Dive Start: {datetime.now().strftime('%H:%M:%S')} ---")
    
    # 1. Update Equity for the Telegram bot
    try:
        account = trading_client.get_account()
        save_bot_status(account.equity)
    except Exception as e:
        print(f"⚠️ Could not update account status: {e}")
    
    # 2. Analyze each symbol
    for sym in symbols:
        print(f"🧐 Analyzing {sym}...")
        data = yf.download(sym, period="1d", interval="1h", progress=False)
        
        if not data.empty:
            verdict = ask_shifu_analysis(sym, data.tail(5).to_string())
            print(f"🦁 Shifu says: {verdict}")
        else:
            print(f"⚠️ Could not find data for {sym}")

if __name__ == "__main__":
    print("🦁 Shifu Analyst Engine Online. Deep dives every 1 hour.")
    
    while True:
        try:
            # Load fresh watchlist every hour
            with open(WATCHLIST_FILE, "r") as f:
                watchlist = json.load(f)["symbols"]
            
            run_analysis_cycle(watchlist)
            
            print("\n💤 Analysis complete. Shifu is resting for 1 hour...")
            time.sleep(3600)
            
        except Exception as e:
            print(f"⚠️ Engine Error: {e}")
            time.sleep(60)