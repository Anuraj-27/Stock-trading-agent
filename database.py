import sqlite3

DB_NAME = "portfolio.db"

def init_db():
    """Initialize the SQLite database and create tables for cash and holdings if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table for tracking cash balance (we'll start with $10,000)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cash REAL NOT NULL
        )
    ''')
    
    # Table for tracking stock holdings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY,
            shares INTEGER NOT NULL,
            avg_price REAL NOT NULL
        )
    ''')
    
    # Initialize default cash if table is empty
    cursor.execute('SELECT cash FROM account WHERE id = 1')
    row = cursor.fetchone()
    if row is None:
        cursor.execute('INSERT INTO account (id, cash) VALUES (1, 10000.0)')
        print("Initialized new portfolio with $10,000.00 virtual cash.")
        
    conn.commit()
    conn.close()

def get_portfolio_status():
    """Fetch current cash and all holdings from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT cash FROM account WHERE id = 1')
    cash = cursor.fetchone()[0]
    
    cursor.execute('SELECT ticker, shares, avg_price FROM holdings')
    rows = cursor.fetchall()
    
    holdings = {}
    for row in rows:
        holdings[row[0]] = {"shares": row[1], "avg_price": row[2]}
        
    conn.close()
    return {"cash": cash, "holdings": holdings}

if __name__ == "__main__":
    # Test initializing the database
    init_db()
    print("Current Portfolio Status:", get_portfolio_status())