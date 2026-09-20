import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

api_key = os.getenv("APCA_API_KEY_ID")
api_secret = os.getenv("APCA_API_SECRET_KEY")

print(f"Loaded API Key: {api_key[:5]}... (length: {len(api_key) if api_key else 0})")

try:
    client = TradingClient(api_key, api_secret, paper=True)
    account = client.get_account()
    print("\nSUCCESS! Connected to Alpaca Paper Trading.")
    print(f"Alpaca Cash Balance: ${float(account.cash):,.2f}")
    print(f"Alpaca Portfolio Value: ${float(account.portfolio_value):,.2f}")
except Exception as e:
    print(f"\nCONNECTION FAILED: {str(e)}")