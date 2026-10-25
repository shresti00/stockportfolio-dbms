import os
import datetime
import yfinance as yf
import mariadb
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

    conn = mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME")
    )
    cur = conn.cursor()

    cur.execute("SELECT ticker FROM assets WHERE ticker = %s", (symbol,))
    if cur.fetchone():
        cur.execute(
            "UPDATE assets SET company_name = %s, sector = %s WHERE ticker = %s",
            (name, sector, symbol)
        )
    else:
        cur.execute(
            "INSERT INTO assets (ticker, company_name, sector) VALUES (%s, %s, %s)",
            (symbol, name, sector)
        )

    cur.execute(
        "SELECT ticker FROM daily_prices WHERE ticker = %s AND price_date = %s",
        (symbol, today)
    )
    if cur.fetchone():
        cur.execute(
            "UPDATE daily_prices SET close_price = %s WHERE ticker = %s AND price_date = %s",
            (current_price, symbol, today)
        )
    else:
        cur.execute(
            "INSERT INTO daily_prices (ticker, price_date, close_price) VALUES (%s, %s, %s)",
            (symbol, today, current_price)
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Successfully updated {symbol}: ${current_price:.2f}")

stocks = ["AAPL", "MSFT", "GOOGL", "NVDA"]
for s in stocks:
    update_stock(s)