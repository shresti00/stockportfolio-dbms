--current portfolio value per user
select u.username,
       round(sum(h.qty * lp.close_price), 2) as portfolio_value
from (
    select user_id, ticker,
           sum(case when txn_type = 'BUY' then quantity else -quantity end) as qty
    from transactions
    group by user_id, ticker
) h
join users u on u.user_id = h.user_id
join daily_prices lp on lp.ticker = h.ticker
 and lp.price_date = (select max(price_date) from daily_prices where ticker = h.ticker)
group by u.username;

--best and worst performing stocks (over the yr)
select ticker,
round((last_price-first_price)/first_price*100,2) as prct_change
from (select d.ticker,
(select close_price from daily_prices where ticker=d.ticker order by price_date asc limit 1 ) as first_price,
(select close_price from daily_prices where ticker=d.ticker order by price_date desc limit 1 ) as last_price
from (select distinct ticker from daily_prices) d
) t
order by prct_change desc;


--sectorwise investment allocation
select a.sector,
round(sum(
    case when tr.txn_type='BUY' then tr.quantity*tr.price_per_share
    else -tr.quantity*tr.price_per_share
    end
),2)as net_invested
from transactions tr
join assets a on a.ticker=tr.ticker
group by a.sector
order by net_invested desc;

--realized vs unrealized gains
select u.username, b.ticker,
       round(coalesce(s.sold_qty, 0) * (coalesce(s.avg_sell, 0) - b.avg_buy), 2) as realized_gain,
       round((b.bought_qty - coalesce(s.sold_qty, 0)) * (lp.close_price - b.avg_buy), 2) as unrealized_gain
from (
    select user_id, ticker, sum(quantity) as bought_qty,
           sum(quantity * price_per_share) / sum(quantity) as avg_buy
    from transactions where txn_type = 'BUY' group by user_id, ticker
) b
left join (
    select user_id, ticker, sum(quantity) as sold_qty,
           sum(quantity * price_per_share) / sum(quantity) as avg_sell
    from transactions where txn_type = 'SELL' group by user_id, ticker
) s on s.user_id = b.user_id and s.ticker = b.ticker
join users u on u.user_id = b.user_id
join daily_prices lp on lp.ticker = b.ticker
 and lp.price_date = (select max(price_date) from daily_prices where ticker = b.ticker);

 --7day nd 30day moving avg
 select ticker, price_date, close_price,
       round(avg(close_price) over (partition by ticker order by price_date rows between 6 preceding and current row), 2) as ma_7,
       round(avg(close_price) over (partition by ticker order by price_date rows between 29 preceding and current row), 2) as ma_30
from daily_prices
where ticker = '$TCS'
order by price_date desc
limit 10;

--stocks that reached their target price
select u.username, w.ticker, w.target_price, lp.close_price as current_price
from watchlist w
join users u on u.user_id = w.user_id
join daily_prices lp on lp.ticker = w.ticker
 and lp.price_date = (select max(price_date) from daily_prices where ticker = w.ticker)
where lp.close_price >= w.target_price;

--most invested stocks overall
select ticker, round(sum(quantity * price_per_share), 2) as total_invested
from transactions
where txn_type = 'BUY'
group by ticker
order by total_invested desc
limit 3;

--high, low and range per stock
select ticker, max(close_price) as high, min(close_price) as low,
       round(max(close_price) - min(close_price), 2) as price_range
from daily_prices
group by ticker;

--most volatile stocks
select ticker, round(stddev(close_price), 2) as volatility
from daily_prices
group by ticker
order by volatility desc;

--latest day price change in percent
select ticker, price_date, close_price, day_change_pct
from (
    select ticker, price_date, close_price,
           round((close_price - lag(close_price) over (partition by ticker order by price_date))
                 / lag(close_price) over (partition by ticker order by price_date) * 100, 2) as day_change_pct
    from daily_prices
) x
where price_date = (select max(price_date) from daily_prices);

--how many sectors each user is spread across
select u.username, count(distinct a.sector) as sectors_held
from transactions t
join users u on u.user_id = t.user_id
join assets a on a.ticker = t.ticker
group by u.username
order by sectors_held desc;

--watchlist stocks the user doesn't own yet
select u.username, w.ticker, w.target_price
from watchlist w
join users u on u.user_id = w.user_id
where not exists (
    select 1 from transactions t
    where t.user_id = w.user_id and t.ticker = w.ticker
);

-- money split by large, mid and small cap
select a.cap_category, round(sum(t.quantity * t.price_per_share), 2) as invested
from transactions t
join assets a on a.ticker = t.ticker
where t.txn_type = 'BUY'
group by a.cap_category;

--what each scheme holds, biggest weight first
select s.scheme_nm, a.company_name, sh.weight_pct
from scheme_holdings sh
join scheme s on s.scheme_id = sh.scheme_id
join assets a on a.ticker = sh.ticker
where sh.as_of_date = (select max(as_of_date) from scheme_holdings where scheme_id = sh.scheme_id)
order by s.scheme_nm, sh.weight_pct desc;

--active scheme investments per user
select u.username, count(*) as schemes, round(sum(usi.amount), 2) as total_amount
from user_scheme_investments usi
join users u on u.user_id = usi.user_id
where usi.status = 'ACTIVE'
group by u.username;

--which company holds stakes in which
select ia.company_name as investor, ea.company_name as investee, ci.stake_prct, ci.shares_held
from company_investments ci
join assets ia on ia.ticker = ci.investor_ticker
join assets ea on ea.ticker = ci.investee_ticker
where ci.as_of_date = (select max(as_of_date) from company_investments)
order by ci.stake_prct desc;

-- stocks a user owns directly and also through a scheme
select distinct u.username, a.company_name, s.scheme_nm
from transactions t
join user_scheme_investments usi on usi.user_id = t.user_id
join scheme_holdings sh on sh.scheme_id = usi.scheme_id and sh.ticker = t.ticker
join users u on u.user_id = t.user_id
join assets a on a.ticker = t.ticker
join scheme s on s.scheme_id = usi.scheme_id;

--nav growth of each scheme
select s.scheme_nm, f.nav as start_nav, l.nav as latest_nav,
       round((l.nav - f.nav) / f.nav * 100, 2) as growth_pct
from scheme s
join scheme_nav_history f on f.scheme_id = s.scheme_id
 and f.nav_date = (select min(nav_date) from scheme_nav_history where scheme_id = s.scheme_id)
join scheme_nav_history l on l.scheme_id = s.scheme_id
 and l.nav_date = (select max(nav_date) from scheme_nav_history where scheme_id = s.scheme_id)
order by growth_pct desc;

--total invested per fund house
select fh.fund_house_nm, count(distinct s.scheme_id) as schemes,
       round(sum(usi.amount), 2) as total_invested
from fund_house fh
join scheme s on s.fund_house_id = fh.fund_house_id
left join user_scheme_investments usi on usi.scheme_id = s.scheme_id
group by fh.fund_house_nm;