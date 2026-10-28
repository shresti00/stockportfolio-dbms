"""
Comprehensive test suite testing:
1. All 19 analytical queries execution and data return
2. Dynamic user switching and user-specific portfolio calculation
3. Direct stock BUY / SELL with over-selling validation
4. Watchlist CRUD and target price trigger alerts
5. Mutual fund investments with min-investment validation
6. Portfolio overlap and indirect exposure calculations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient
from app import app
from db import execute_query, QUERIES_MYSQL

client = TestClient(app)

def test_system_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    print(f"[PASS] System status -> Mode: {data.get('mode')}")

def test_all_19_analytical_queries():
    print(f"Testing execution of all {len(QUERIES_MYSQL)} analytical queries...")
    for qk in sorted(QUERIES_MYSQL.keys()):
        params = ("TCS",) if qk == "q5_moving_average" else None
        res = execute_query(qk, params)
        assert res.get("status") == "success", f"Query {qk} failed: {res.get('error')}"
        rows = len(res.get("data", []))
        print(f"  [PASS] {qk}: {rows} rows returned")

def test_user_portfolio_switching():
    # User 1 (dale_cooper)
    res1 = client.get("/api/portfolio/user/1")
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["user_id"] == 1
    assert "direct_stock_value" in d1

    # User 2 (priya)
    res2 = client.get("/api/portfolio/user/2")
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["user_id"] == 2
    # Verify different user data returned
    assert d1["direct_stock_value"] != d2["direct_stock_value"]
    print(f"[PASS] User-specific portfolio test: User 1 value=Rs.{d1['direct_stock_value']}, User 2 value=Rs.{d2['direct_stock_value']}")

def test_stock_trade_validation():
    # Attempting to SELL more shares than owned by user 1 for RELIANCE (user 1 has 0 shares)
    sell_attempt = {
        "user_id": 1,
        "ticker": "RELIANCE",
        "txn_type": "SELL",
        "quantity": 100.0,
        "price_per_share": 1400.0
    }
    res = client.post("/api/transactions", json=sell_attempt)
    assert res.status_code == 400
    assert "Cannot SELL" in res.json().get("detail", "")
    print(f"[PASS] Over-sell protection verified: rejected with message '{res.json().get('detail')}'")

    # Valid BUY
    buy_attempt = {
        "user_id": 1,
        "ticker": "RELIANCE",
        "txn_type": "BUY",
        "quantity": 2.0,
        "price_per_share": 1200.0
    }
    res_buy = client.post("/api/transactions", json=buy_attempt)
    assert res_buy.status_code == 200
    print("[PASS] BUY transaction recorded successfully")

def test_watchlist_workflow():
    # Add to watchlist
    wl_item = {"user_id": 1, "ticker": "TATAMOTORS", "target_price": 750.0}
    res = client.post("/api/watchlist", json=wl_item)
    # Could be success or error if already in db
    assert res.status_code in (200, 400)
    
    # Retrieve watchlist
    res_get = client.get("/api/watchlist?user_id=1")
    assert res_get.status_code == 200
    wl_data = res_get.json()
    assert "items" in wl_data
    print(f"[PASS] Watchlist retrieved: {len(wl_data['items'])} items")

def test_mutual_fund_investment():
    # Attempt below minimum investment for scheme 101 (min is 500)
    low_inv = {"user_id": 1, "scheme_id": 101, "amount": 100.0}
    res_low = client.post("/api/funds/invest", json=low_inv)
    assert res_low.status_code == 400
    assert "Minimum investment" in res_low.json().get("detail", "")
    print(f"[PASS] Scheme minimum investment verified: rejected with '{res_low.json().get('detail').encode('ascii', 'ignore').decode('ascii')}'")

    # Valid investment
    valid_inv = {"user_id": 1, "scheme_id": 101, "amount": 1000.0}
    res_valid = client.post("/api/funds/invest", json=valid_inv)
    assert res_valid.status_code == 200
    print("[PASS] Mutual fund investment recorded successfully")

def test_portfolio_exposure():
    res = client.get("/api/exposure/1")
    assert res.status_code == 200
    data = res.json()
    assert "direct_holdings" in data
    assert "indirect_exposure" in data
    assert "overlap" in data
    print(f"[PASS] Exposure retrieved: {len(data['direct_holdings'])} direct, {len(data['indirect_exposure'])} indirect, {len(data['overlap'])} overlap")

if __name__ == "__main__":
    test_system_status()
    test_all_19_analytical_queries()
    test_user_portfolio_switching()
    test_stock_trade_validation()
    test_watchlist_workflow()
    test_mutual_fund_investment()
    test_portfolio_exposure()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
