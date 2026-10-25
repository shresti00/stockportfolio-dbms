
import yfinance as yf

# Database ticker : Yahoo Finance ticker
tickers = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "TATAMOTORS": "TMPV.NS",
    "ZOMATO": "ETERNAL.NS",
    "IRFC": "IRFC.NS",
    "SUZLON": "SUZLON.NS"
}

lines = []

for db_ticker, yf_ticker in tickers.items():
    hist = yf.Ticker(yf_ticker).history(period="1y")

    for date, row in hist.iterrows():
        d = date.date()
        p = round(float(row["Close"]), 2)

        lines.append(
            f"insert ignore into daily_prices "
            f"(ticker, price_date, close_price) "
            f"values ('{db_ticker}', '{d}', {p});"
        )

with open("daily_prices.sql", "w") as f:
    f.write("\n".join(lines))

print(len(lines), "rows written")
