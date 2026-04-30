import telebot, json, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

WATCHLIST_FILE = "watchlist.json"
STATUS_FILE = "bot_status.json"

def load_json(file):
    with open(file, "r") as f: return json.load(f)

@bot.message_handler(commands=['status'])
def status(message):
    data = load_json(STATUS_FILE)
    bot.reply_to(message, f"💰 Equity: `${data['equity']}`\n🕒 Last Sync: `{data['last_update']}`", parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_watch(message):
    data = load_json(WATCHLIST_FILE)
    bot.reply_to(message, f"🔍 Current Hunt: `{', '.join(data['symbols'])}`", parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add(message):
    sym = message.text.replace('/add ', '').strip().upper()
    data = load_json(WATCHLIST_FILE)
    
    if sym not in data['symbols']:
        data['symbols'].append(sym)
        
        # Move this to two lines!
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(data, f, indent=4)
            
        bot.reply_to(message, f"✅ Added **{sym}** to Shifu's list.", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def ai_chat(message):
    # Context Injection: AI knows your balance and list
    status_info = load_json(STATUS_FILE)
    watchlist = load_json(WATCHLIST_FILE)
    
    prompt = (f"You are Shifu, a wise Malaysian trading bot. "
              f"Bank: ${status_info['equity']}. Watching: {watchlist['symbols']}.")
    
    chat_completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": message.text}]
    )
    bot.reply_to(message, chat_completion.choices[0].message.content)

print("✅ Shifu Voice is Online.")
bot.infinity_polling()