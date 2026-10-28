"""
Database connection manager and query execution engine for Stock Portfolio Tracker DBMS.
Supports connecting directly to AWS RDS MySQL, with fallback to local SQLite replica.
Maintains exact SQL implementations of all 19 queries mapped to business functions.
"""

import os
import sqlite3
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "stockport")

LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "stockport_local.db")

QUERIES_MYSQL = {
    # 1. Current portfolio value per user
    "q1_portfolio_value": """
        SELECT u.user_id, u.username,
               ROUND(SUM(h.qty * lp.close_price), 2) AS portfolio_value
        FROM (
            SELECT user_id, ticker,
                   SUM(CASE WHEN txn_type = 'BUY' THEN quantity ELSE -quantity END) AS qty
            FROM transactions
            GROUP BY user_id, ticker
        ) h
        JOIN users u ON u.user_id = h.user_id
        JOIN daily_prices lp ON lp.ticker = h.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = h.ticker)
        GROUP BY u.user_id, u.username;
    """,

    # 2. Best and worst performing stocks over the year
    "q2_stock_performance": """
        SELECT ticker,
               ROUND((last_price - first_price) / first_price * 100, 2) AS prct_change
        FROM (
            SELECT d.ticker,
                   (SELECT close_price FROM daily_prices WHERE ticker = d.ticker ORDER BY price_date ASC LIMIT 1) AS first_price,
                   (SELECT close_price FROM daily_prices WHERE ticker = d.ticker ORDER BY price_date DESC LIMIT 1) AS last_price
            FROM (SELECT DISTINCT ticker FROM daily_prices) d
        ) t
        ORDER BY prct_change DESC;
    """,

    # 3. Sectorwise investment allocation
    "q3_sector_allocation": """
        SELECT a.sector,
               ROUND(SUM(
                   CASE WHEN tr.txn_type = 'BUY' THEN tr.quantity * tr.price_per_share
                   ELSE -tr.quantity * tr.price_per_share
                   END
               ), 2) AS net_invested
        FROM transactions tr
        JOIN assets a ON a.ticker = tr.ticker
        GROUP BY a.sector
        ORDER BY net_invested DESC;
    """,

    # 4. Realized vs unrealized gains
    "q4_realized_unrealized": """
        SELECT u.user_id, u.username, b.ticker,
               ROUND(COALESCE(s.sold_qty, 0) * (COALESCE(s.avg_sell, 0) - b.avg_buy), 2) AS realized_gain,
               ROUND((b.bought_qty - COALESCE(s.sold_qty, 0)) * (lp.close_price - b.avg_buy), 2) AS unrealized_gain,
               ROUND(b.bought_qty - COALESCE(s.sold_qty, 0), 2) AS net_qty,
               ROUND(b.avg_buy, 2) AS avg_buy_price,
               lp.close_price AS current_price
        FROM (
            SELECT user_id, ticker, SUM(quantity) AS bought_qty,
                   SUM(quantity * price_per_share) / SUM(quantity) AS avg_buy
            FROM transactions WHERE txn_type = 'BUY' GROUP BY user_id, ticker
        ) b
        LEFT JOIN (
            SELECT user_id, ticker, SUM(quantity) AS sold_qty,
                   SUM(quantity * price_per_share) / SUM(quantity) AS avg_sell
            FROM transactions WHERE txn_type = 'SELL' GROUP BY user_id, ticker
        ) s ON s.user_id = b.user_id AND s.ticker = b.ticker
        JOIN users u ON u.user_id = b.user_id
        JOIN daily_prices lp ON lp.ticker = b.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = b.ticker);
    """,

    # 5. 7-day and 30-day moving average
    "q5_moving_average": """
        SELECT ticker, price_date, close_price,
               ROUND(AVG(close_price) OVER (PARTITION BY ticker ORDER BY price_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma_7,
               ROUND(AVG(close_price) OVER (PARTITION BY ticker ORDER BY price_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 2) AS ma_30
        FROM daily_prices
        WHERE ticker = %s
        ORDER BY price_date DESC
        LIMIT 30;
    """,

    # 6. Stocks that reached their target price
    "q6_target_price_reached": """
        SELECT u.user_id, u.username, w.ticker, w.target_price, lp.close_price AS current_price
        FROM watchlist w
        JOIN users u ON u.user_id = w.user_id
        JOIN daily_prices lp ON lp.ticker = w.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = w.ticker)
        WHERE lp.close_price >= w.target_price;
    """,

    # 7. Most invested stocks overall
    "q7_most_invested": """
        SELECT ticker, ROUND(SUM(quantity * price_per_share), 2) AS total_invested
        FROM transactions
        WHERE txn_type = 'BUY'
        GROUP BY ticker
        ORDER BY total_invested DESC
        LIMIT 5;
    """,

    # 8. High, low and range per stock
    "q8_price_ranges": """
        SELECT ticker, MAX(close_price) AS high, MIN(close_price) AS low,
               ROUND(MAX(close_price) - MIN(close_price), 2) AS price_range
        FROM daily_prices
        GROUP BY ticker;
    """,

    # 9. Most volatile stocks
    "q9_volatility": """
        SELECT ticker, ROUND(STDDEV(close_price), 2) AS volatility
        FROM daily_prices
        GROUP BY ticker
        ORDER BY volatility DESC;
    """,

    # 10. Latest day price change in percent
    "q10_latest_day_change": """
        SELECT ticker, price_date, close_price, day_change_pct
        FROM (
            SELECT ticker, price_date, close_price,
                   ROUND((close_price - LAG(close_price) OVER (PARTITION BY ticker ORDER BY price_date))
                         / LAG(close_price) OVER (PARTITION BY ticker ORDER BY price_date) * 100, 2) AS day_change_pct
            FROM daily_prices
        ) x
        WHERE price_date = (SELECT MAX(price_date) FROM daily_prices);
    """,

    # 11. How many sectors each user is spread across
    "q11_sectors_per_user": """
        SELECT u.user_id, u.username, COUNT(DISTINCT a.sector) AS sectors_held
        FROM transactions t
        JOIN users u ON u.user_id = t.user_id
        JOIN assets a ON a.ticker = t.ticker
        GROUP BY u.user_id, u.username
        ORDER BY sectors_held DESC;
    """,

    # 12. Watchlist stocks the user doesn't own yet
    "q12_unowned_watchlist": """
        SELECT u.user_id, u.username, w.ticker, w.target_price
        FROM watchlist w
        JOIN users u ON u.user_id = w.user_id
        WHERE NOT EXISTS (
            SELECT 1 FROM transactions t
            WHERE t.user_id = w.user_id AND t.ticker = w.ticker
        );
    """,

    # 13. Money split by large, mid and small cap
    "q13_cap_split": """
        SELECT a.cap_category, ROUND(SUM(t.quantity * t.price_per_share), 2) AS invested
        FROM transactions t
        JOIN assets a ON a.ticker = t.ticker
        WHERE t.txn_type = 'BUY'
        GROUP BY a.cap_category;
    """,

    # 14. What each scheme holds, biggest weight first
    "q14_scheme_holdings": """
        SELECT s.scheme_id, s.scheme_nm, a.ticker, a.company_name, a.sector, sh.weight_pct
        FROM scheme_holdings sh
        JOIN scheme s ON s.scheme_id = sh.scheme_id
        JOIN assets a ON a.ticker = sh.ticker
        WHERE sh.as_of_date = (SELECT MAX(as_of_date) FROM scheme_holdings WHERE scheme_id = sh.scheme_id)
        ORDER BY s.scheme_nm, sh.weight_pct DESC;
    """,

    # 15. Active scheme investments per user
    "q15_active_schemes_per_user": """
        SELECT u.user_id, u.username, COUNT(*) AS schemes, ROUND(SUM(usi.amount), 2) AS total_amount
        FROM user_scheme_investments usi
        JOIN users u ON u.user_id = usi.user_id
        WHERE usi.status = 'ACTIVE'
        GROUP BY u.user_id, u.username;
    """,

    # 16. Which company holds stakes in which
    "q16_company_investments": """
        SELECT ia.company_name AS investor, ea.company_name AS investee, ci.stake_prct, ci.shares_held
        FROM company_investments ci
        JOIN assets ia ON ia.ticker = ci.investor_ticker
        JOIN assets ea ON ea.ticker = ci.investee_ticker
        WHERE ci.as_of_date = (SELECT MAX(as_of_date) FROM company_investments)
        ORDER BY ci.stake_prct DESC;
    """,

    # 17. Stocks a user owns directly and also through a scheme
    "q17_direct_scheme_overlap": """
        SELECT DISTINCT u.user_id, u.username, a.ticker, a.company_name, s.scheme_nm, sh.weight_pct
        FROM transactions t
        JOIN user_scheme_investments usi ON usi.user_id = t.user_id
        JOIN scheme_holdings sh ON sh.scheme_id = usi.scheme_id AND sh.ticker = t.ticker
        JOIN users u ON u.user_id = t.user_id
        JOIN assets a ON a.ticker = t.ticker
        JOIN scheme s ON s.scheme_id = usi.scheme_id;
    """,

    # 18. NAV growth of each scheme
    "q18_scheme_nav_growth": """
        SELECT s.scheme_id, s.scheme_nm, f.nav AS start_nav, l.nav AS latest_nav,
               ROUND((l.nav - f.nav) / f.nav * 100, 2) AS growth_pct
        FROM scheme s
        JOIN scheme_nav_history f ON f.scheme_id = s.scheme_id
         AND f.nav_date = (SELECT MIN(nav_date) FROM scheme_nav_history WHERE scheme_id = s.scheme_id)
        JOIN scheme_nav_history l ON l.scheme_id = s.scheme_id
         AND l.nav_date = (SELECT MAX(nav_date) FROM scheme_nav_history WHERE scheme_id = s.scheme_id)
        ORDER BY growth_pct DESC;
    """,

    # 19. Total invested per fund house
    "q19_fund_house_invested": """
        SELECT fh.fund_house_nm, COUNT(DISTINCT s.scheme_id) AS schemes,
               ROUND(SUM(usi.amount), 2) AS total_invested
        FROM fund_house fh
        JOIN scheme s ON s.fund_house_id = fh.fund_house_id
        LEFT JOIN user_scheme_investments usi ON usi.scheme_id = s.scheme_id
        GROUP BY fh.fund_house_nm;
    """
}

QUERIES_SQLITE = dict(QUERIES_MYSQL)
QUERIES_SQLITE["q9_volatility"] = """
    SELECT ticker,
           ROUND(SQRT(AVG(close_price * close_price) - AVG(close_price) * AVG(close_price)), 2) AS volatility
    FROM daily_prices
    GROUP BY ticker
    ORDER BY volatility DESC;
"""
QUERIES_SQLITE["q5_moving_average"] = QUERIES_SQLITE["q5_moving_average"].replace("%s", "?")


def get_db_connection():
    if not DB_HOST or not DB_USER:
        return None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3
        )
        return conn
    except Exception:
        return None


def execute_query(query_key, params=None):
    conn = get_db_connection()
    if conn:
        try:
            sql = QUERIES_MYSQL.get(query_key)
            with conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                res = cur.fetchall()
            conn.close()
            return {"source": "AWS_RDS_MYSQL", "data": res, "status": "success"}
        except Exception as err:
            conn.close()
            return {"source": "AWS_RDS_MYSQL", "error": str(err), "status": "error", "data": []}

    try:
        sql = QUERIES_SQLITE.get(query_key)
        local_conn = sqlite3.connect(LOCAL_DB_PATH)
        local_conn.row_factory = sqlite3.Row
        cur = local_conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
        local_conn.close()
        return {"source": "LOCAL_SQLITE_REPLICA", "data": rows, "status": "success"}
    except Exception as e:
        return {"source": "LOCAL_SQLITE_REPLICA", "error": str(e), "status": "error", "data": []}


def execute_raw(sql, params=None, is_write=False):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if is_write:
                    conn.commit()
                    res = {"lastrowid": cur.lastrowid, "rowcount": cur.rowcount}
                else:
                    res = cur.fetchall()
            conn.close()
            return {"source": "AWS_RDS_MYSQL", "data": res, "status": "success"}
        except Exception as err:
            conn.close()
            return {"source": "AWS_RDS_MYSQL", "error": str(err), "status": "error"}

    try:
        sql_sqlite = sql.replace("%s", "?")
        local_conn = sqlite3.connect(LOCAL_DB_PATH)
        local_conn.row_factory = sqlite3.Row
        cur = local_conn.cursor()
        cur.execute(sql_sqlite, params or ())
        if is_write:
            local_conn.commit()
            res = {"lastrowid": cur.lastrowid, "rowcount": cur.rowcount}
        else:
            res = [dict(r) for r in cur.fetchall()]
        local_conn.close()
        return {"source": "LOCAL_SQLITE_REPLICA", "data": res, "status": "success"}
    except Exception as e:
        return {"source": "LOCAL_SQLITE_REPLICA", "error": str(e), "status": "error"}


def get_db_status():
    conn = get_db_connection()
    if conn:
        conn.close()
        return {
            "mode": "AWS_RDS_MYSQL",
            "host": DB_HOST,
            "database": DB_NAME,
            "connected": True
        }
    return {
        "mode": "LOCAL_SQLITE_REPLICA",
        "file": os.path.basename(LOCAL_DB_PATH),
        "note": "AWS RDS MySQL credentials not set. Serving via DBMS local replica.",
        "connected": True
    }
