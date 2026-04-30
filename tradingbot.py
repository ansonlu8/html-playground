import os
import json
import time
import yfinance as yf
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()
# Using exact keys from your .env
ALPACA_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY')

if not ALPACA_KEY or not ALPACA_SECRET:
    print("❌ ERROR: Alpaca keys missing in .env")
    exit()

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

WATCHLIST_FILE = "watchlist.json"

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def ask_shifu_analysis(symbol, price_data):
    """Sends raw market data to the AI to get a 'Wise' opinion."""
    prompt = f"""
    Analyze {symbol} market data:
    {price_data}
    
    As Shifu, give a 1-sentence technical verdict. 
    Should we enter a trade or stay patient? Use Malaysian wit.
    """
    
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

def run_analysis_cycle(symbols):
    for sym in symbols:
        data = yf.download(sym, period="1d", interval="1h", progress=False)
        if data.empty: continue
        
        current_price = data['Close'].iloc[-1]
        
        # Here is the 'AI Brain' working:
        print(f"🧐 Shifu is contemplating {sym}...")
        verdict = ask_shifu_analysis(sym, data.tail(5).to_string())
        print(f"🦁 Shifu's Wisdom: {verdict}")
if __name__ == "__main__":
    print("🦁 Master Engine Online (Light Mode for Python 3.14)")
    while True:
        try:
            with open(WATCHLIST_FILE, "r") as f:
                watchlist = json.load(f)["symbols"]
            run_analysis_cycle(watchlist)
            time.sleep(600) # Rest 10 mins
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(60)

# --- SETUP ---
load_dotenv()
trading_client = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), paper=True)

WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"

# Safety and Strategy
MAX_POSITIONS = 5
STRATEGY_MAP = {
    "BTC/USD": {"trail": 0.8},
    "ETH/USD": {"trail": 1.5},
    "SOL/USD": {"trail": 3.0},
    "DEFAULT": {"trail": 2.0}
}

def update_shared_status():
    """Tells the Chatbot what our bank balance is."""
    try:
        acc = trading_client.get_account()
        with open(STATUS_FILE, "w") as f:
            json.dump({
                "equity": f"{float(acc.equity):.2f}",
                "last_update": datetime.now().strftime("%H:%M:%S")
            }, f, indent=4)
    except Exception as e:
        print(f"Status Update Error: {e}")

def get_signals(symbol):
    """Calculates if we should buy."""
    df = yf.download(symbol, period="1d", interval="5m", progress=False)
    if df.empty or len(df) < 20: return None
    
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    last = df.iloc[-1]
    # Signal: Above EMA (Trend) and RSI < 70 (Not overbought)
    if last['Close'] > last['EMA_20'] and last['RSI'] < 70:
        return True, last['Close']
    return False, last['Close']

def run_simple_cycle(symbols):
    for yf_sym in symbols:
        # Fetch only the last 2 prices to check trend
        data = yf.download(yf_sym, period="1d", interval="5m", progress=False)
        if data.empty: continue
        
        last_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        
        # Simple Logic: If price is higher than 5 mins ago, it's a "mini-trend"
        if last_price > prev_price:
            print(f"📈 {yf_sym} is moving up: ${last_price:.2f}")
        else:
            print(f"📉 {yf_sym} is cooling: ${last_price:.2f}")

if __name__ == "__main__":
    print("🦁 Master Engine Online (Light Mode).")
    while True:
        try:
            with open("watchlist.json", "r") as f:
                watchlist = json.load(f)["symbols"]
            run_simple_cycle(watchlist)
            time.sleep(600)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(60)

            # --- THE BRAIN LOOP ---
if __name__ == "__main__":
    print("🦁 Shifu Analyst Engine Online. Contemplating the markets...")
    
    while True:
        try:
            # 1. Load the symbols you added via Telegram
            with open("watchlist.json", "r") as f:
                watchlist = json.load(f)["symbols"]
            
            # 2. Run the AI analysis cycle
            run_analysis_cycle(watchlist)
            
            # 3. Rest for 1 hour (Analysis doesn't need to be every 10 mins)
            print("💤 Shifu is meditating for 1 hour...")
            time.sleep(3600) 
            
        except Exception as e:
            print(f"⚠️ Engine Error: {e}")
            time.sleep(60)