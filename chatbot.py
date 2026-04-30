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

# --- THE BUTTON LISTENER ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        # Split e.g., "buy_TSLA_700" -> ['buy', 'TSLA', '700']
        _, symbol, amount = call.data.split("_")
        amount = int(amount)
        
        bot.answer_callback_query(call.id, f"Executing ${amount} buy...")
        
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                notional=amount, 
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )
            trading_client.submit_order(order_data)
            bot.edit_message_text(f"🚀 **ORDER SUCCESS!** Bought ${amount} of {symbol}. Huat ah, Boss!", 
                                 call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ Trade Failed: {e}")
            
    elif call.data == "ignore":
        bot.answer_callback_query(call.id, "Advice ignored.")
        bot.edit_message_text("🙈 Advice ignored. Staying patient like a master.", 
                             call.message.chat.id, call.message.message_id)

# (Keep your existing @bot.message_handler commands below this...)
@bot.message_handler(commands=['status'])
def status(message):
    data = load_json(STATUS_FILE)
    bot.reply_to(message, f"💰 Equity: `${data['equity']}`", parse_mode='Markdown')

bot.infinity_polling()