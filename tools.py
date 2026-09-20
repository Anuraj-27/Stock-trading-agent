import os
import yfinance as yf
from dotenv import load_dotenv
from langchain_core.tools import tool
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load environment variables
load_dotenv()

# Initialize Alpaca Paper Trading Client
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")

trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current live market price for a given stock ticker (e.g., AAPL, MSFT, EG)."""
    try:
        stock = yf.Ticker(ticker.upper())
        todays_data = stock.history(period="1d")
        if todays_data.empty:
            return f"Could not find data for ticker {ticker.upper()}."
        price = todays_data['Close'].iloc[-1]
        return f"The current live price of {ticker.upper()} is ${price:.2f}"
    except Exception as e:
        return f"Error fetching price: {str(e)}"

@tool
def view_portfolio() -> str:
    """View the current Alpaca paper trading cash balance, total portfolio value, and open stock positions."""
    try:
        account = trading_client.get_account()
        positions = trading_client.get_all_positions()
        
        cash = float(account.cash)
        portfolio_value = float(account.portfolio_value)
        
        holdings = {}
        for p in positions:
            holdings[p.symbol] = {
                "shares": int(p.qty),
                "avg_price": float(p.avg_entry_price),
                "market_value": float(p.market_value)
            }
            
        return f"Alpaca Paper Cash: ${cash:,.2f} | Total Portfolio Value: ${portfolio_value:,.2f} | Holdings: {holdings}"
    except Exception as e:
        return f"Alpaca Authentication Error: {str(e)}. Please check your APCA_API_KEY_ID and APCA_API_SECRET_KEY in the .env file."

@tool
def buy_stock(ticker: str, shares: int) -> str:
    """Execute a real paper trading market order to buy shares using your Alpaca sandbox account."""
    ticker = ticker.upper()
    if shares <= 0:
        return "Number of shares to buy must be greater than zero."
        
    try:
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=shares,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(order_data=market_order_data)
        return f"Successfully placed Alpaca paper BUY order for {shares} shares of {ticker}! Order ID: {order.id}"
    except Exception as e:
        return f"Alpaca buy order failed: {str(e)}"

@tool
def sell_stock(ticker: str, shares: int) -> str:
    """Execute a real paper trading market order to sell shares from your Alpaca sandbox account."""
    ticker = ticker.upper()
    if shares <= 0:
        return "Number of shares to sell must be greater than zero."
        
    try:
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=shares,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(order_data=market_order_data)
        return f"Successfully placed Alpaca paper SELL order for {shares} shares of {ticker}! Order ID: {order.id}"
    except Exception as e:
        return f"Alpaca sell order failed: {str(e)}"