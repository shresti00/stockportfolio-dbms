insert into users
(user_id, username, email, pwd_hash, is_active, last_login, failed_attempts)
values
(1, 'dale_cooper', 'dale@gmail.com', 'demo_hash_001', true, '2026-10-24 10:30:00', 0),
(2, 'priya', 'priya@gmail.com', 'demo_hash_002', true, '2026-10-23 18:45:00', 1),
(3, 'laura_palmer', 'laura@gmail.com', 'demo_hash_003', true, '2026-10-22 09:15:00', 0),
(4, 'bobby_briggs', 'briggs@gmail.com', 'demo_hash_004', false, null, 3),
(5, 'rahul', 'rahul@gmail.com', 'demo_hash_005', true, '2026-10-25 08:00:00', 0);

insert into assets
(ticker, company_name, sector, cap_category)
values
('RELIANCE', 'Reliance Industries', 'Energy', 'LARGE'),
('TCS', 'Tata Consultancy Services', 'IT', 'LARGE'),
('INFY', 'Infosys', 'IT', 'LARGE'),
('HDFCBANK', 'HDFC Bank', 'Banking', 'LARGE'),
('TATAMOTORS', 'Tata Motors', 'Automobile', 'MID'),
('ZOMATO', 'Eternal Limited', 'Technology', 'MID'),
('IRFC', 'Indian Railway Finance Corporation', 'Finance', 'MID'),
('SUZLON', 'Suzlon Energy', 'Renewable Energy', 'SMALL');

insert into transactions
(transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
values
(1, 1, 'TCS', 'BUY', 5, 3100.00, '2026-10-10'),
(2, 1, 'INFY', 'BUY', 10, 1480.00, '2026-10-12'),
(3, 1, 'TCS', 'SELL', 2, 3200.00, '2026-10-20'),
(4, 2, 'RELIANCE', 'BUY', 8, 1440.00, '2026-10-11'),
(5, 2, 'HDFCBANK', 'BUY', 6, 1680.00, '2026-10-13'),
(6, 2, 'HDFCBANK', 'SELL', 1, 1710.00, '2026-10-22'),
(7, 3, 'TATAMOTORS', 'BUY', 15, 675.00, '2026-10-14'),
(8, 3, 'ZOMATO', 'BUY', 20, 248.00, '2026-10-15'),
(9, 4, 'IRFC', 'BUY', 30, 138.00, '2026-10-16'),
(10, 5, 'SUZLON', 'BUY', 50, 54.00, '2026-10-18'),
(11, 5, 'RELIANCE', 'BUY', 3, 1460.00, '2026-10-21'),
(12, 3, 'TATAMOTORS', 'SELL', 5, 690.00, '2026-10-22');

insert into watchlist
(watchlist_id, user_id, ticker, target_price, added_date)
values
(1, 1, 'RELIANCE', 1500.00, '2026-10-10'),
(2, 1, 'HDFCBANK', 1750.00, '2026-10-11'),
(3, 2, 'TCS', 3300.00, '2026-10-12'),
(4, 2, 'INFY', 1550.00, '2026-10-13'),
(5, 3, 'SUZLON', 60.00, '2026-10-14'),
(6, 3, 'IRFC', 150.00, '2026-10-15'),
(7, 4, 'ZOMATO', 270.00, '2026-10-16'),
(8, 5, 'TATAMOTORS', 720.00, '2026-10-18');

insert into company_investments
(investor_ticker, investee_ticker, shares_held, stake_prct, as_of_date)
values
('RELIANCE', 'TCS', 10000, 2.50, '2026-10-01'),
('RELIANCE', 'INFY', 8000, 1.80, '2026-10-01'),
('TCS', 'INFY', 5000, 1.20, '2026-10-01'),
('HDFCBANK', 'RELIANCE', 6000, 1.50, '2026-10-01'),
('TCS', 'HDFCBANK', 4000, 0.90, '2026-10-01'),
('RELIANCE', 'TATAMOTORS', 7000, 2.10, '2026-10-01');

insert into fund_house
(fund_house_id, fund_house_nm)
values
(1, 'SBI Mutual Fund'),
(2, 'HDFC Mutual Fund'),
(3, 'ICICI Prudential'),
(4, 'Axis Mutual Fund');

insert into scheme
(scheme_id, fund_house_id, scheme_nm, category, risk_level, nav, min_investment, expense_ratio)
values
(101, 1, 'SBI Bluechip Fund', 'LARGE_CAP', 'MODERATE', 85.2500, 500.00, 0.75),
(102, 2, 'HDFC Mid Cap Fund', 'MID_CAP', 'HIGH', 125.5000, 100.00, 0.80),
(103, 3, 'ICICI Small Cap Fund', 'SMALL_CAP', 'HIGH', 95.7500, 100.00, 0.90),
(104, 4, 'Axis Flexi Cap Fund', 'FLEXI', 'MODERATE', 72.4000, 500.00, 0.65),
(105, 1, 'SBI Large Cap Fund', 'LARGE_CAP', 'LOW', 65.8000, 500.00, 0.60);

insert into scheme_holdings
(scheme_id, ticker, weight_pct, as_of_date)
values
(101, 'RELIANCE', 9.50, '2026-10-01'),
(101, 'TCS', 8.00, '2026-10-01'),
(101, 'HDFCBANK', 7.50, '2026-10-01'),
(102, 'TATAMOTORS', 6.50, '2026-10-01'),
(102, 'INFY', 5.00, '2026-10-01'),
(103, 'SUZLON', 4.00, '2026-10-01'),
(103, 'ZOMATO', 3.50, '2026-10-01'),
(104, 'RELIANCE', 8.00, '2026-10-01'),
(104, 'INFY', 6.00, '2026-10-01'),
(104, 'TCS', 7.00, '2026-10-01'),
(105, 'HDFCBANK', 9.00, '2026-10-01'),
(105, 'RELIANCE', 8.50, '2026-10-01');

insert into user_scheme_investments
(investment_id, user_id, scheme_id, amount, units, nav_at_purchase, start_date, sip_amount, status)
values
(1, 1, 101, 10000.00, 117.3021, 85.2500, '2026-08-01', 2000.00, 'ACTIVE'),
(2, 1, 104, 5000.00, 69.0608, 72.4000, '2026-09-01', 1000.00, 'ACTIVE'),
(3, 2, 102, 15000.00, 119.5219, 125.5000, '2026-07-15', 2500.00, 'ACTIVE'),
(4, 2, 103, 3000.00, 31.3316, 95.7500, '2026-08-15', null, 'PAUSED'),
(5, 3, 105, 8000.00, 121.5805, 65.8000, '2026-06-01', 1500.00, 'ACTIVE'),
(6, 3, 101, 4000.00, 46.9208, 85.2500, '2026-07-01', null, 'REDEEMED'),
(7, 4, 104, 6000.00, 82.8729, 72.4000, '2026-09-10', 1000.00, 'ACTIVE'),
(8, 5, 102, 10000.00, 79.6813, 125.5000, '2026-08-20', 2000.00, 'ACTIVE');

insert into scheme_nav_history
(scheme_id, nav_date, nav)
values
(101, '2026-10-20', 84.5000),
(101, '2026-10-21', 84.8000),
(101, '2026-10-22', 85.0000),
(101, '2026-10-23', 85.2500),

(102, '2026-10-20', 123.0000),
(102, '2026-10-21', 124.2000),
(102, '2026-10-22', 125.0000),
(102, '2026-10-23', 125.5000),

(103, '2026-10-20', 94.0000),
(103, '2026-10-21', 95.0000),
(103, '2026-10-22', 95.2000),
(103, '2026-10-23', 95.7500),

(104, '2026-10-20', 71.8000),
(104, '2026-10-21', 72.0000),
(104, '2026-10-22', 72.2000),
(104, '2026-10-23', 72.4000),

(105, '2026-10-20', 65.0000),
(105, '2026-10-21', 65.2000),
(105, '2026-10-22', 65.5000),
(105, '2026-10-23', 65.8000);

commit;