import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

# This loads the variables from your .env file
load_dotenv()

# Get keys and print a check (don't worry, this won't show the whole key)
api_key = os.getenv("ALPACA_API_KEY")
secret_key = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not secret_key:
    print("❌ Keys not found! Make sure your .env file is in the same folder.")
else:
    # Initialize the client
    client = TradingClient(api_key, secret_key, paper=True)

    try:
        account = client.get_account()
        print("✅ SUCCESS: Bot connected to Alpaca!")
        print(f"💰 Current Balance: ${account.cash}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")