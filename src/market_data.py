import os
import datetime
import yfinance as yf
import oracledb
from dotenv import load_dotenv

load_dotenv()

def update_stock(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    
    name = info.get('shortName', symbol)
    sector = info.get('sector', 'Unknown')
    
    hist = stock.history(period="1d")
    if hist.empty:
        print(f"Could not get data for {symbol}")
        return

    current_price = float(hist['Close'].iloc[-1])
    today = datetime.date.today()

    conn = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )
    cur = conn.cursor()

    # 1. Update or Insert ASSETS table
    cur.execute("SELECT ticker FROM ASSETS WHERE ticker = :1", [symbol])
    if cur.fetchone():
        cur.execute(
            "UPDATE ASSETS SET company_name = :1, sector = :2 WHERE ticker = :3",
            [name, sector, symbol]
        )
    else:
        cur.execute(
            "INSERT INTO ASSETS (ticker, company_name, sector) VALUES (:1, :2, :3)",
            [symbol, name, sector]
        )

    # 2. Update or Insert DAILY_PRICES table
    cur.execute(
        "SELECT ticker FROM DAILY_PRICES WHERE ticker = :1 AND price_date = :2",
        [symbol, today]
    )
    if cur.fetchone():
        cur.execute(
            "UPDATE DAILY_PRICES SET close_price = :1 WHERE ticker = :2 AND price_date = :3",
            [current_price, symbol, today]
        )
    else:
        cur.execute(
            "INSERT INTO DAILY_PRICES (ticker, price_date, close_price) VALUES (:1, :2, :3)",
            [symbol, today, current_price]
        )

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Successfully updated {symbol}: ${current_price:.2f}")

stocks = ["AAPL", "MSFT", "GOOGL", "NVDA"]
for s in stocks:
    update_stock(s)