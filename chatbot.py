import telebot, json, os
from groq import Groq
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
trading_client = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), paper=True)

WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"

def load_json(file):
    with open(file, "r") as f: return json.load(f)

# --- NEW: LIQUIDATION HELPER ---
def execute_liquidation(symbol):
    try:
        trading_client.close_position(symbol)
        return f"Done! Sold all your {symbol} positions. Huat ah! 💸"
    except Exception as e:
        if "position does not exist" in str(e):
            return f"Aiya, you don't even own any {symbol} lah!"
        return f"Error liquidating {symbol}: {e}"


def add_to_watchlist_file(symbol):
    try:
        data = load_json(WATCHLIST_FILE)
        watchlist = data.get("symbols", [])
        
        # CLEANING: Remove punctuation and force uppercase
        import string
        clean_symbol = symbol.strip(string.punctuation).upper()
        
        if clean_symbol not in watchlist:
            watchlist.append(clean_symbol)
            data["symbols"] = watchlist
            with open(WATCHLIST_FILE, "w") as f:
                json.dump(data, f, indent=4)
            return f"Done, Boss! Added {clean_symbol} to your watchlist."
        else:
            return f"Aiya, {clean_symbol} is already inside lah!"
    except Exception as e:
        return f"Failed to update watchlist: {e}"
    

# --- THE AI BRAIN LOGIC ---
def get_shifu_response(user_input):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    system_prompt = (
        "You are Shifu, a witty Malaysian trading expert. Use 'lah', 'aiya', and 'bro' naturally. "
        "1. If the user asks to 'liquidate' or 'sell all', use 'ACTION_LIQUIDATE:[SYMBOL]'. "
        "2. If the user asks to 'add [SYMBOL] to watchlist', use 'ACTION_ADD_WATCHLIST:[SYMBOL]'. " # New instruction
        "Example: 'ACTION_ADD_WATCHLIST:AAPL'. Then follow with your funny Malaysian commentary."
    )
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )
    return completion.choices[0].message.content

# --- THE BUTTON LISTENER ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        _, symbol, amount = call.data.split("_")
        amount = int(amount)
        bot.answer_callback_query(call.id, f"Shifu is processing ${amount} of {symbol}...")
        try:
            clean_symbol = symbol.replace("-", "/")
            is_crypto = "/" in clean_symbol or any(x in clean_symbol for x in ["BTC", "ETH", "SOL"])
            tif = TimeInForce.GTC if is_crypto else TimeInForce.DAY
            
            order_data = MarketOrderRequest(
                symbol=clean_symbol,
                notional=amount,
                side=OrderSide.BUY,
                time_in_force=tif
            )
            trading_client.submit_order(order_data)
            bot.edit_message_text(f"🚀 **ORDER SUCCESS!** Bought ${amount} of {symbol}. Huat ah, Boss!", 
                                 call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ Trade Failed for {symbol}: {e}")
            
    elif call.data == "ignore":
        bot.answer_callback_query(call.id, "Advice ignored.")
        bot.edit_message_text("🙈 Advice ignored. Staying patient like a master.",
                             call.message.chat.id, call.message.message_id)

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['status'])
def status(message):
    data = load_json(STATUS_FILE)
    bot.reply_to(message, f"💰 Equity: `${data['equity']}`", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    user_input = message.text
    try:
        raw_response = get_shifu_response(user_input)
        
        # 1. Check for Liquidation
        if "ACTION_LIQUIDATE:" in raw_response:
            parts = raw_response.split("ACTION_LIQUIDATE:")
            symbol = parts[1].split()[0].strip().replace(":", "")
            bot.reply_to(message, execute_liquidation(symbol))
            
        # 2. Check for Watchlist (THIS IS THE PART YOU ARE MISSING)
        elif "ACTION_ADD_WATCHLIST:" in raw_response:
            parts = raw_response.split("ACTION_ADD_WATCHLIST:")
            symbol = parts[1].split()[0].strip().replace(":", "")
            
            # This calls the function to write to your JSON file
            result_msg = add_to_watchlist_file(symbol) 
            bot.reply_to(message, result_msg)

        # 3. Always show Shifu's funny reply
        clean_msg = raw_response.split("]")[-1].strip()
        if clean_msg:
            bot.send_message(message.chat.id, clean_msg)

    except Exception as e:
        print(f"❌ AI Error: {e}")
        bot.reply_to(message, "🦁 Shifu is meditating. Try again!")

if __name__ == "__main__":
    print("🦁 Shifu is awake and listening...")
    bot.infinity_polling()