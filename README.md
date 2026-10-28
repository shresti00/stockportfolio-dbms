# Stock Portfolio Tracker DBMS

An enterprise-grade Stock Portfolio Tracker and DBMS analytical system built on top of relational SQL schemas, analytical queries, and market data.

The system connects directly to **AWS RDS MySQL** (`stockport` database) while providing an automated, replica fallback initialized directly from the project's repository SQL scripts (`sql/01_tables.sql`, `sql/04_seed.sql`, `daily_prices.sql`).

---

## 1. Architecture Overview

- **Database Engine**: AWS RDS MySQL / MariaDB (Database name: `stockport`).
- **Backend API**: Python 3.12+ / FastAPI / Uvicorn / PyMySQL.
- **Frontend UI**: Responsive HTML5, TailwindCSS, Chart.js, FontAwesome.
- **Query Execution Engine**: Directly executes all 19 stock portfolio analytics queries.

---

## 2. Environment Configuration

To connect the application to your AWS RDS MySQL instance, create a `.env` file in the project root directory (never commit this file to git):

```env
DB_HOST=your-rds-endpoint.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=stockport
```

*Note: If `DB_HOST` or `DB_USER` are omitted, the application automatically runs using the local DBMS replica populated from the repository's seed and 1,984 daily price records.*

---

## 3. Running the Application

### Step 1: Install Dependencies
```bash
py -3.12 -m pip install fastapi uvicorn pymysql cryptography
```

### Step 2: Launch Server
```bash
py -3.12 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Access the UI & API
- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 4. Running Verification Tests
Execute the comprehensive test suite validating all 19 queries and API endpoints:
```bash
py -3.12 src/run_tests.py
```

---

## 5. Catalog of the 19 Portfolio Analytics Queries

All 19 analytical queries from `sql/stock_query.sql` are mapped to dedicated API endpoints:

| # | Query Key | Description / Purpose | Endpoint |
|---|---|---|---|
| **Q1** | `q1_portfolio_value` | Current portfolio valuation per user | `/api/analytics/q1_portfolio_value` |
| **Q2** | `q2_stock_performance` | Best and worst performing stocks over the year | `/api/analytics/q2_stock_performance` |
| **Q3** | `q3_sector_allocation` | Sectorwise net investment allocation | `/api/analytics/q3_sector_allocation` |
| **Q4** | `q4_realized_unrealized` | Realized vs unrealized profit and loss | `/api/analytics/q4_realized_unrealized` |
| **Q5** | `q5_moving_average` | 7-day and 30-day moving average window functions | `/api/analytics/q5_moving_average?ticker=TCS` |
| **Q6** | `q6_target_price_reached` | Stocks that hit or exceeded target price | `/api/analytics/q6_target_price_reached` |
| **Q7** | `q7_most_invested` | Most invested stocks across all users | `/api/analytics/q7_most_invested` |
| **Q8** | `q8_price_ranges` | 52-week High, Low, and Price Range per stock | `/api/analytics/q8_price_ranges` |
| **Q9** | `q9_volatility` | Stock volatility (standard deviation of daily prices) | `/api/analytics/q9_volatility` |
| **Q10** | `q10_latest_day_change` | Latest day price change percentage | `/api/analytics/q10_latest_day_change` |
| **Q11** | `q11_sectors_per_user` | Sector diversification count per user | `/api/analytics/q11_sectors_per_user` |
| **Q12** | `q12_unowned_watchlist` | Watchlist stocks tracked by user but not yet bought | `/api/analytics/q12_unowned_watchlist` |
| **Q13** | `q13_cap_split` | Investment breakdown by Large, Mid, and Small Cap | `/api/analytics/q13_cap_split` |
| **Q14** | `q14_scheme_holdings` | Mutual fund scheme portfolio holdings breakdown | `/api/analytics/q14_scheme_holdings` |
| **Q15** | `q15_active_schemes_per_user`| Active scheme investment counts and capital | `/api/analytics/q15_active_schemes_per_user` |
| **Q16** | `q16_company_investments` | Cross-company corporate equity stakes | `/api/analytics/q16_company_investments` |
| **Q17** | `q17_direct_scheme_overlap` | Stocks held directly that are also held via schemes | `/api/analytics/q17_direct_scheme_overlap` |
| **Q18** | `q18_scheme_nav_growth` | Historical NAV percentage growth per scheme | `/api/analytics/q18_scheme_nav_growth` |
| **Q19** | `q19_fund_house_invested` | Total capital and scheme counts per Fund House | `/api/analytics/q19_fund_house_invested` |
