# Import the 'os' module to interact with your operating system and access secure environment variables
import os

# Import 'load_dotenv' to read the secrets stored in your .env file
from dotenv import load_dotenv

# Import 'yfinance' and give it the nickname 'yf' so we don't have to type the full name every time
import yfinance as yf

# Load the hidden environment variables from the .env file into the operating system's memory
load_dotenv()

# Securely grab the Groq API key from the OS memory without displaying it in the code
groq_key = os.getenv("GROQ_API_KEY")

# Check if the key was found and print a status message
if groq_key:
    print("SUCCESS: Groq API key loaded securely from .env!")
else:
    print("WARNING: Groq API key not found. Check your .env file.")

# Define a function to fetch the live price. It takes a 'ticker' (a short company code like AAPL)
def test_fetch_price(ticker):
    print(f"\nFetching live data for {ticker}...")
    
    # Create a Ticker object representing the specific company we want to look up
    stock = yf.Ticker(ticker)
    
    # Ask Yahoo Finance for the market data spanning the last 1 day ("1d")
    todays_data = stock.history(period="1d")
    
    # If the spreadsheet is empty (maybe the ticker is wrong or the market is closed), stop and print an error
    if todays_data.empty:
        print(f"Could not fetch data for {ticker}.")
        return
        
    # Look at the 'Close' column of today's data, and use .iloc[-1] to grab the very last (most recent) price
    price = todays_data['Close'].iloc[-1]
    
    # Print the final price rounded to 2 decimal places
    print(f"Success! The current price of {ticker.upper()} is ${price:.2f}")

# This standard Python line ensures the code below only runs if this script is executed directly
if __name__ == "__main__":
    # Test the function by passing in the ticker for Apple
    test_fetch_price("AAPL")
    
    # Test the function by passing in the ticker for Microsoft
    test_fetch_price("MSFT")