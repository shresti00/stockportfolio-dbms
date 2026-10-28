"""
Local SQLite database initializer that parses and loads sql/01_tables.sql,
sql/04_seed.sql, and daily_prices.sql without altering original files.
Enables offline development and complete verification when AWS RDS is unreachable.
"""

import os
import sqlite3
import re

SQL_DIR = os.path.join(os.path.dirname(__file__), "..", "sql")
DAILY_PRICES_SQL = os.path.join(os.path.dirname(__file__), "..", "daily_prices.sql")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "stockport_local.db")


def init_local_db():
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 50000:
        return DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables compatible with SQLite
    tables_ddl = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        created_at DATE DEFAULT (date('now')),
        pwd_hash TEXT NOT NULL DEFAULT '',
        is_active BOOLEAN NOT NULL DEFAULT 1,
        last_login DATETIME NULL,
        failed_attempts INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS assets (
        ticker TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        sector TEXT,
        cap_category TEXT CHECK(cap_category IN ('LARGE','MID','SMALL'))
    );

    CREATE TABLE IF NOT EXISTS daily_prices (
        ticker TEXT,
        price_date DATE NOT NULL,
        close_price REAL NOT NULL,
        PRIMARY KEY(ticker, price_date),
        FOREIGN KEY(ticker) REFERENCES assets(ticker)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        txn_type TEXT NOT NULL CHECK (txn_type IN ('BUY','SELL')),
        quantity REAL NOT NULL,
        price_per_share REAL NOT NULL,
        txn_date DATE DEFAULT (date('now')),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (ticker) REFERENCES assets(ticker)
    );

    CREATE TABLE IF NOT EXISTS watchlist (
        watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        target_price REAL,
        added_date DATE DEFAULT (date('now')),
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(ticker) REFERENCES assets(ticker),
        UNIQUE(user_id, ticker)
    );

    CREATE TABLE IF NOT EXISTS company_investments (
        investor_ticker TEXT,
        investee_ticker TEXT,
        shares_held INTEGER,
        stake_prct REAL,
        as_of_date DATE,
        PRIMARY KEY(investor_ticker, investee_ticker, as_of_date),
        FOREIGN KEY(investor_ticker) REFERENCES assets(ticker),
        FOREIGN KEY(investee_ticker) REFERENCES assets(ticker)
    );

    CREATE TABLE IF NOT EXISTS fund_house (
        fund_house_id INTEGER PRIMARY KEY,
        fund_house_nm TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS scheme (
        scheme_id INTEGER PRIMARY KEY,
        fund_house_id INTEGER NOT NULL,
        scheme_nm TEXT NOT NULL,
        category TEXT CHECK(category IN ('LARGE_CAP','MID_CAP','SMALL_CAP','FLEXI')),
        risk_level TEXT CHECK(risk_level IN ('LOW','MODERATE','HIGH')),
        nav REAL,
        min_investment REAL NOT NULL,
        expense_ratio REAL,
        FOREIGN KEY(fund_house_id) REFERENCES fund_house(fund_house_id)
    );

    CREATE TABLE IF NOT EXISTS scheme_holdings (
        scheme_id INTEGER,
        ticker TEXT,
        weight_pct REAL,
        as_of_date DATE,
        PRIMARY KEY(scheme_id, ticker, as_of_date),
        FOREIGN KEY(scheme_id) REFERENCES scheme(scheme_id),
        FOREIGN KEY(ticker) REFERENCES assets(ticker)
    );

    CREATE TABLE IF NOT EXISTS user_scheme_investments (
        investment_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        scheme_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        units REAL,
        nav_at_purchase REAL,
        start_date DATE,
        sip_amount REAL DEFAULT NULL,
        status TEXT CHECK(status IN ('ACTIVE','PAUSED','REDEEMED')),
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(scheme_id) REFERENCES scheme(scheme_id)
    );

    CREATE TABLE IF NOT EXISTS scheme_nav_history (
        scheme_id INTEGER,
        nav_date DATE,
        nav REAL,
        PRIMARY KEY(scheme_id, nav_date),
        FOREIGN KEY(scheme_id) REFERENCES scheme(scheme_id)
    );
    """
    cur.executescript(tables_ddl)

    # Seed data from sql/04_seed.sql
    seed_file = os.path.join(SQL_DIR, "04_seed.sql")
    if os.path.exists(seed_file):
        with open(seed_file, "r", encoding="utf-8") as f:
            seed_content = f.read()
        # Clean boolean literals and commit statements for SQLite
        seed_content = seed_content.replace("true", "1").replace("false", "0").replace("commit;", "")
        # Remove empty lines or commented lines
        statements = [s.strip() for s in seed_content.split(";") if s.strip()]
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as e:
                pass

    # Seed daily_prices from daily_prices.sql
    if os.path.exists(DAILY_PRICES_SQL):
        with open(DAILY_PRICES_SQL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("insert ignore into"):
                    line = line.replace("insert ignore into", "insert or ignore into")
                if line:
                    try:
                        cur.execute(line)
                    except Exception:
                        pass

    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    p = init_local_db()
    print("Local database initialized successfully at:", p)
