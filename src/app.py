"""
Stock Portfolio Tracker DBMS - User-Centered Financial Platform API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys

# Ensure src is on Python sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import execute_query, execute_raw, get_db_status, QUERIES_MYSQL

app = FastAPI(
    title="Stock Portfolio Tracker Platform",
    description="Investor-centric portfolio, mutual funds, and market intelligence DBMS platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class TransactionCreate(BaseModel):
    user_id: int
    ticker: str
    txn_type: str  # BUY or SELL
    quantity: float
    price_per_share: float
    txn_date: Optional[str] = None

class WatchlistItemCreate(BaseModel):
    user_id: int
    ticker: str
    target_price: float

class SchemeInvestmentCreate(BaseModel):
    user_id: int
    scheme_id: int
    amount: float
    sip_amount: Optional[float] = None
    start_date: Optional[str] = None

# System & DB Status
@app.get("/api/status")
def status():
    return get_db_status()

# Demo Users
@app.get("/api/users")
def get_users():
    sql = "SELECT user_id, username, email, is_active FROM users"
    return execute_raw(sql).get("data", [])

# All Assets
@app.get("/api/assets")
def get_assets():
    sql = """
        SELECT a.ticker, a.company_name, a.sector, a.cap_category,
               lp.close_price as latest_price, lp.price_date
        FROM assets a
        LEFT JOIN daily_prices lp ON lp.ticker = a.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = a.ticker)
        ORDER BY a.ticker ASC
    """
    return execute_raw(sql).get("data", [])

# Single Stock Detail
@app.get("/api/stocks/{ticker}")
def get_stock_detail(ticker: str):
    asset_sql = "SELECT ticker, company_name, sector, cap_category FROM assets WHERE ticker = %s"
    asset_res = execute_raw(asset_sql, (ticker,)).get("data", [])
    if not asset_res:
        raise HTTPException(status_code=404, detail="Stock asset not found")
    
    asset = asset_res[0]
    ranges = execute_query("q8_price_ranges").get("data", [])
    r_item = next((r for r in ranges if r.get("ticker") == ticker), {})
    
    vol = execute_query("q9_volatility").get("data", [])
    v_item = next((v for v in vol if v.get("ticker") == ticker), {})
    
    latest = execute_query("q10_latest_day_change").get("data", [])
    l_item = next((l for l in latest if l.get("ticker") == ticker), {})
    
    ma = execute_query("q5_moving_average", (ticker,)).get("data", [])

    return {
        "asset": asset,
        "range": r_item,
        "volatility": v_item,
        "latest_change": l_item,
        "history": ma
    }

# User-Centric Portfolio Overview (Dashboard & Portfolio Page)
@app.get("/api/portfolio/user/{user_id}")
def user_portfolio(user_id: int):
    # Total Valuation
    all_values = execute_query("q1_portfolio_value").get("data", [])
    user_val_item = next((v for v in all_values if v.get("user_id") == user_id), None)
    portfolio_value = float(user_val_item.get("portfolio_value", 0)) if user_val_item else 0.0

    # Realized & Unrealized P&L
    all_gains = execute_query("q4_realized_unrealized").get("data", [])
    user_gains = [g for g in all_gains if g.get("user_id") == user_id]

    total_realized = sum(float(g.get("realized_gain", 0) or 0) for g in user_gains)
    total_unrealized = sum(float(g.get("unrealized_gain", 0) or 0) for g in user_gains)

    # Active Holdings: Only stocks where net_qty > 0
    active_holdings = [g for g in user_gains if float(g.get("net_qty", 0) or 0) > 0]
    invested_capital = sum(float(g.get("net_qty", 0)) * float(g.get("avg_buy_price", 0)) for g in active_holdings)

    # Sector Diversification
    all_sectors = execute_query("q11_sectors_per_user").get("data", [])
    user_sector_item = next((s for s in all_sectors if s.get("user_id") == user_id), None)
    sectors_held = int(user_sector_item.get("sectors_held", 0)) if user_sector_item else 0

    # Mutual Fund Investments for this user
    mf_sql = """
        SELECT usi.investment_id, usi.user_id, usi.scheme_id, s.scheme_nm, fh.fund_house_nm,
               s.category, s.risk_level, s.nav as current_nav,
               usi.amount, usi.units, usi.nav_at_purchase, usi.start_date, usi.sip_amount, usi.status
        FROM user_scheme_investments usi
        JOIN scheme s ON s.scheme_id = usi.scheme_id
        JOIN fund_house fh ON fh.fund_house_id = s.fund_house_id
        WHERE usi.user_id = %s
    """
    user_mf_investments = execute_raw(mf_sql, (user_id,)).get("data", [])
    mf_invested_total = sum(float(m.get("amount", 0) or 0) for m in user_mf_investments if m.get("status") == "ACTIVE")

    # Target Price Alert Hits for this user
    all_alerts = execute_query("q6_target_price_reached").get("data", [])
    user_alerts = [a for a in all_alerts if a.get("user_id") == user_id]

    # Global allocations (Market Cap & Sectors)
    cap_alloc = execute_query("q13_cap_split").get("data", [])
    sector_alloc = execute_query("q3_sector_allocation").get("data", [])

    return {
        "user_id": user_id,
        "direct_stock_value": portfolio_value,
        "direct_invested_capital": round(invested_capital, 2),
        "total_realized_pnl": round(total_realized, 2),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "active_holdings": active_holdings,
        "sectors_held_count": sectors_held,
        "mf_invested_total": round(mf_invested_total, 2),
        "mf_investments": user_mf_investments,
        "alerts": user_alerts,
        "cap_allocation": cap_alloc,
        "sector_allocation": sector_alloc
    }

# Stock Explorer
@app.get("/api/stocks/explorer")
def stock_explorer():
    perf = execute_query("q2_stock_performance").get("data", [])
    ranges = execute_query("q8_price_ranges").get("data", [])
    vol = execute_query("q9_volatility").get("data", [])
    latest = execute_query("q10_latest_day_change").get("data", [])
    most_inv = execute_query("q7_most_invested").get("data", [])
    assets = execute_raw("SELECT ticker, company_name, sector, cap_category FROM assets").get("data", [])

    return {
        "assets": assets,
        "performance": perf,
        "price_ranges": ranges,
        "volatility": vol,
        "latest_day_change": latest,
        "most_invested": most_inv
    }

# Transactions Management
@app.get("/api/transactions")
def list_transactions(user_id: Optional[int] = None):
    sql = """
        SELECT t.transaction_id, t.user_id, u.username, t.ticker, a.company_name,
               t.txn_type, t.quantity, t.price_per_share,
               ROUND(t.quantity * t.price_per_share, 2) AS total_value,
               t.txn_date
        FROM transactions t
        JOIN users u ON u.user_id = t.user_id
        JOIN assets a ON a.ticker = t.ticker
    """
    if user_id:
        sql += " WHERE t.user_id = %s ORDER BY t.transaction_id DESC"
        return execute_raw(sql, (user_id,)).get("data", [])
    else:
        sql += " ORDER BY t.transaction_id DESC"
        return execute_raw(sql).get("data", [])

@app.post("/api/transactions")
def create_transaction(txn: TransactionCreate):
    if txn.txn_type not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Transaction action must be BUY or SELL")
    if txn.quantity <= 0 or txn.price_per_share <= 0:
        raise HTTPException(status_code=400, detail="Quantity and price must be greater than zero")

    # If SELL: Validate user has sufficient shares currently owned
    if txn.txn_type == "SELL":
        check_sql = """
            SELECT SUM(CASE WHEN txn_type = 'BUY' THEN quantity ELSE -quantity END) as net_shares
            FROM transactions
            WHERE user_id = %s AND ticker = %s
        """
        res = execute_raw(check_sql, (txn.user_id, txn.ticker)).get("data", [])
        net_owned = float(res[0].get("net_shares", 0) or 0) if res else 0.0
        if txn.quantity > net_owned:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot SELL {txn.quantity} shares. You currently own {net_owned:.2f} shares of {txn.ticker}."
            )

    if txn.txn_date:
        sql = """
            INSERT INTO transactions (user_id, ticker, txn_type, quantity, price_per_share, txn_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (txn.user_id, txn.ticker, txn.txn_type, txn.quantity, txn.price_per_share, txn.txn_date)
    else:
        sql = """
            INSERT INTO transactions (user_id, ticker, txn_type, quantity, price_per_share)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (txn.user_id, txn.ticker, txn.txn_type, txn.quantity, txn.price_per_share)

    res = execute_raw(sql, params, is_write=True)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return {"status": "success", "message": f"{txn.txn_type} order recorded for {txn.ticker}"}

# Watchlist Management
@app.get("/api/watchlist")
def get_watchlist(user_id: Optional[int] = None):
    targets_hit = execute_query("q6_target_price_reached").get("data", [])
    unowned = execute_query("q12_unowned_watchlist").get("data", [])

    query = """
        SELECT w.watchlist_id, w.user_id, u.username, w.ticker, a.company_name,
               w.target_price, w.added_date, lp.close_price as current_price
        FROM watchlist w
        JOIN users u ON u.user_id = w.user_id
        JOIN assets a ON a.ticker = w.ticker
        JOIN daily_prices lp ON lp.ticker = w.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = w.ticker)
    """
    if user_id:
        query += " WHERE w.user_id = %s"
        all_items = execute_raw(query, (user_id,)).get("data", [])
        user_hits = [t for t in targets_hit if t.get("user_id") == user_id]
        user_unowned = [u for u in unowned if u.get("user_id") == user_id]
    else:
        all_items = execute_raw(query).get("data", [])
        user_hits = targets_hit
        user_unowned = unowned

    return {
        "items": all_items,
        "targets_reached": user_hits,
        "unowned": user_unowned
    }

@app.post("/api/watchlist")
def add_watchlist(item: WatchlistItemCreate):
    if item.target_price <= 0:
        raise HTTPException(status_code=400, detail="Target price must be greater than zero")
    sql = "INSERT INTO watchlist (user_id, ticker, target_price) VALUES (%s, %s, %s)"
    res = execute_raw(sql, (item.user_id, item.ticker, item.target_price), is_write=True)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("error"))
    return {"status": "success", "message": f"Added {item.ticker} to watchlist"}

@app.delete("/api/watchlist/{watchlist_id}")
def delete_watchlist(watchlist_id: int):
    sql = "DELETE FROM watchlist WHERE watchlist_id = %s"
    res = execute_raw(sql, (watchlist_id,), is_write=True)
    return {"status": "success", "message": "Removed from watchlist"}

# Mutual Funds Exploration & Investment
@app.get("/api/funds")
def list_funds():
    schemes_sql = """
        SELECT s.scheme_id, s.scheme_nm, s.fund_house_id, fh.fund_house_nm,
               s.category, s.risk_level, s.nav, s.min_investment, s.expense_ratio
        FROM scheme s
        JOIN fund_house fh ON fh.fund_house_id = s.fund_house_id
        ORDER BY s.scheme_nm ASC
    """
    schemes = execute_raw(schemes_sql).get("data", [])
    holdings = execute_query("q14_scheme_holdings").get("data", [])
    growth = execute_query("q18_scheme_nav_growth").get("data", [])
    fund_houses = execute_query("q19_fund_house_invested").get("data", [])

    return {
        "schemes": schemes,
        "holdings": holdings,
        "nav_growth": growth,
        "fund_houses": fund_houses
    }

@app.post("/api/funds/invest")
def invest_in_scheme(inv: SchemeInvestmentCreate):
    # Validate scheme exists and check min_investment
    scheme_res = execute_raw("SELECT scheme_id, nav, min_investment FROM scheme WHERE scheme_id = %s", (inv.scheme_id,)).get("data", [])
    if not scheme_res:
        raise HTTPException(status_code=404, detail="Mutual fund scheme not found")
    
    scheme = scheme_res[0]
    min_inv = float(scheme.get("min_investment", 0))
    if inv.amount < min_inv:
        raise HTTPException(status_code=400, detail=f"Minimum investment for this scheme is ₹{min_inv:,.2f}")

    nav = float(scheme.get("nav") or 100.0)
    units = round(inv.amount / nav, 4)

    # Next investment ID
    max_id_res = execute_raw("SELECT COALESCE(MAX(investment_id), 0) + 1 AS next_id FROM user_scheme_investments").get("data", [])
    next_id = int(max_id_res[0]["next_id"]) if max_id_res else 1

    sql = """
        INSERT INTO user_scheme_investments
        (investment_id, user_id, scheme_id, amount, units, nav_at_purchase, start_date, sip_amount, status)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, 'ACTIVE')
    """
    res = execute_raw(sql, (next_id, inv.user_id, inv.scheme_id, inv.amount, units, nav, inv.sip_amount), is_write=True)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("error"))

    return {"status": "success", "message": f"Successfully invested ₹{inv.amount:,.2f} ({units} units) in scheme."}

# Portfolio Exposure & Overlap
@app.get("/api/exposure/{user_id}")
def portfolio_exposure(user_id: int):
    # 1. Direct Owned Companies
    direct_sql = """
        SELECT t.ticker, a.company_name, a.sector,
               SUM(CASE WHEN t.txn_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as net_shares,
               lp.close_price as current_price
        FROM transactions t
        JOIN assets a ON a.ticker = t.ticker
        JOIN daily_prices lp ON lp.ticker = t.ticker
         AND lp.price_date = (SELECT MAX(price_date) FROM daily_prices WHERE ticker = t.ticker)
        WHERE t.user_id = %s
        GROUP BY t.ticker, a.company_name, a.sector
        HAVING net_shares > 0
    """
    direct_holdings = execute_raw(direct_sql, (user_id,)).get("data", [])

    # 2. Indirect Holdings via Schemes Held by User
    indirect_sql = """
        SELECT usi.user_id, s.scheme_id, s.scheme_nm, sh.ticker, a.company_name, a.sector,
               sh.weight_pct, usi.amount as user_scheme_amount,
               ROUND(usi.amount * (sh.weight_pct / 100.0), 2) as estimated_exposure
        FROM user_scheme_investments usi
        JOIN scheme s ON s.scheme_id = usi.scheme_id
        JOIN scheme_holdings sh ON sh.scheme_id = s.scheme_id
        JOIN assets a ON a.ticker = sh.ticker
        WHERE usi.user_id = %s AND usi.status = 'ACTIVE'
          AND sh.as_of_date = (SELECT MAX(as_of_date) FROM scheme_holdings WHERE scheme_id = sh.scheme_id)
        ORDER BY estimated_exposure DESC
    """
    indirect_exposure = execute_raw(indirect_sql, (user_id,)).get("data", [])

    # 3. Direct vs Scheme Overlap
    all_overlap = execute_query("q17_direct_scheme_overlap").get("data", [])
    user_overlap = [o for o in all_overlap if o.get("user_id") == user_id]

    return {
        "user_id": user_id,
        "direct_holdings": direct_holdings,
        "indirect_exposure": indirect_exposure,
        "overlap": user_overlap
    }

# Corporate Cross-Ownership (Separate from Personal Portfolio)
@app.get("/api/corporate-ownership")
def corporate_ownership():
    stakes = execute_query("q16_company_investments").get("data", [])
    return stakes

# Internal / Developer Analytical Query Catalogue
@app.get("/api/internal/analytics/{query_key}")
def run_internal_query(query_key: str, ticker: Optional[str] = "TCS"):
    if query_key not in QUERIES_MYSQL:
        raise HTTPException(status_code=404, detail="Query key not found")
    params = (ticker,) if query_key == "q5_moving_average" else None
    return execute_query(query_key, params)

# Serve Frontend SPA
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "public")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
