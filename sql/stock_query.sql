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

-- 7-day moving average of closing price for every stock
select ticker, price_date, close_price, ma_7
from (
    select ticker, price_date, close_price,
           round(avg(close_price) over (
               partition by ticker
               order by price_date
               rows between 6 preceding and current row
           ), 2) as ma_7,
           row_number() over (partition by ticker order by price_date desc) as rn
    from daily_prices
) x
where rn = 1;

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

-- top 5 stocks by percentage gain over the last 30 days
select l.ticker,
       o.close_price as price_30d_ago,
       l.close_price as latest_price,
       round((l.close_price - o.close_price) / o.close_price * 100, 2) as gain_pct
from daily_prices l
join daily_prices o on o.ticker = l.ticker
where l.price_date = (select max(price_date) from daily_prices where ticker = l.ticker)
  and o.price_date = (select max(price_date) from daily_prices
                      where ticker = l.ticker
                      and price_date <= date_sub(l.price_date, interval 30 day))
order by gain_pct desc
limit 5;




-- purpose: one readable table of every transaction with the user and company details
create view v_transaction_details as
select t.transaction_id, u.username, a.ticker, a.company_name, a.sector,
       t.txn_type, t.quantity, t.price_per_share,
       round(t.quantity * t.price_per_share, 2) as amount, t.txn_date
from transactions t
join users u on u.user_id = t.user_id
join assets a on a.ticker = t.ticker;

-- query using the view
select * from v_transaction_details where username = 'dale_cooper';



-- purpose: total bought and number of stocks in each sector
create view v_sector_summary as
select a.sector, count(distinct a.ticker) as stocks,
       round(sum(case when t.txn_type = 'BUY' then t.quantity * t.price_per_share else 0 end), 2) as total_bought
from assets a
left join transactions t on t.ticker = a.ticker
group by a.sector;

-- query using the view
select * from v_sector_summary order by total_bought desc;



-- purpose: show only active users and hide email, password hash and login details
create view v_public_users as
select user_id, username, created_at
from users
where is_active = true
with check option;

-- query using the view
select * from v_public_users;

delimiter //

-- 1. add a transaction, and refuse a sell if the user doesn't hold enough shares
create procedure add_transaction1(
    in p_user int, in p_ticker varchar(10), in p_type varchar(10),
    in p_qty decimal(10,2), in p_price decimal(10,2))
begin
    declare v_held decimal(12,2) default 0;
    if p_type = 'SELL' then
        select coalesce(sum(case when txn_type = 'BUY' then quantity else -quantity end), 0)
        into v_held
        from transactions
        where user_id = p_user and ticker = p_ticker;
        if v_held < p_qty then
            signal sqlstate '45000' set message_text = 'not enough shares to sell';
        end if;
    end if;
    insert into transactions (user_id, ticker, txn_type, quantity, price_per_share)
    values (p_user, p_ticker, p_type, p_qty, p_price);
end //

-- 2. show a user's current holdings with latest price and value
create procedure user_portfolio1(in p_user int)
begin
    select h.ticker, h.qty, lp.close_price as latest_price,
           round(h.qty * lp.close_price, 2) as current_value
    from (
        select ticker, sum(case when txn_type = 'BUY' then quantity else -quantity end) as qty
        from transactions
        where user_id = p_user
        group by ticker
    ) h
    join daily_prices lp on lp.ticker = h.ticker
     and lp.price_date = (select max(price_date) from daily_prices where ticker = h.ticker)
    where h.qty > 0;
end //

delimiter ;

call add_transaction1(1, '$TCS', 'BUY', 5, 3500.00);
call add_transaction1(2, '$IRFC', 'SELL', 100, 150.00);  -- error: not enough shares to sell
call user_portfolio1(1);


delimiter //

-- 1. latest closing price of a stock
create function get_latest_price(p_ticker varchar(10))
returns decimal(10,2)
reads sql data
begin
    declare v_price decimal(10,2);
    select close_price into v_price
    from daily_prices
    where ticker = p_ticker
    order by price_date desc
    limit 1;
    return v_price;
end //

-- 2. current value of a user's holding in one stock (uses the first function)
create function holding_value(p_user int, p_ticker varchar(10))
returns decimal(14,2)
reads sql data
begin
    declare v_qty decimal(12,2);
    select coalesce(sum(case when txn_type = 'BUY' then quantity else -quantity end), 0)
    into v_qty
    from transactions
    where user_id = p_user and ticker = p_ticker;
    return round(v_qty * get_latest_price(p_ticker), 2);
end //

delimiter ;

select ticker, get_latest_price(ticker) as latest_price from assets;
select username, holding_value(user_id, '$TCS') as tcs_value from users;


-- table to store the log
create table txn_audit(
    audit_id int primary key auto_increment,
    transaction_id int,
    user_id int,
    ticker varchar(10),
    txn_type varchar(10),
    logged_at datetime default current_timestamp
);

delimiter //

-- 1. before insert: block transactions with zero or negative quantity or price
create trigger trg_txn_check
before insert on transactions
for each row
begin
    if new.quantity <= 0 or new.price_per_share <= 0 then
        signal sqlstate '45000' set message_text = 'quantity and price must be more than zero';
    end if;
end //

-- 2. after insert: log every new transaction in the audit table
create trigger trg_txn_log
after insert on transactions
for each row
begin
    insert into txn_audit (transaction_id, user_id, ticker, txn_type)
    values (new.transaction_id, new.user_id, new.ticker, new.txn_type);
end //

delimiter ;

-- test
insert into transactions (user_id, ticker, txn_type, quantity, price_per_share)
values (1, '$TCS', 'BUY', -1, 100);   -- error from trigger 1
call add_transaction(1, '$INFY', 'BUY', 2, 1500.00);
select * from txn_audit;               


delimiter //

-- 1. loop through every user and calculate the total amount they bought
create procedure user_invest_report()
begin
    declare done int default 0;
    declare v_id int;
    declare v_name varchar(20);
    declare v_total decimal(14,2);
    declare cur cursor for select user_id, username from users;
    declare continue handler for not found set done = 1;

    create temporary table if not exists tmp_report (
        username varchar(20),
        total_invested decimal(14,2)
    );
    truncate tmp_report;

    open cur;
    read_loop: loop
        fetch cur into v_id, v_name;
        if done = 1 then
            leave read_loop;
        end if;
        select coalesce(sum(quantity * price_per_share), 0) into v_total
        from transactions
        where user_id = v_id and txn_type = 'BUY';
        insert into tmp_report values (v_name, v_total);
    end loop;
    close cur;

    select * from tmp_report;
end //

-- 2. loop through the watchlist and flag stocks that reached the target price
create procedure check_target_alerts()
begin
    declare done int default 0;
    declare v_user int;
    declare v_ticker varchar(10);
    declare v_target decimal(10,2);
    declare v_price decimal(10,2);
    declare cur cursor for
        select user_id, ticker, target_price from watchlist where target_price is not null;
    declare continue handler for not found set done = 1;

    create temporary table if not exists tmp_alerts (
        user_id int,
        ticker varchar(10),
        target_price decimal(10,2),
        current_price decimal(10,2),
        status varchar(20)
    );
    truncate tmp_alerts;

    open cur;
    alert_loop: loop
        fetch cur into v_user, v_ticker, v_target;
        if done = 1 then
            leave alert_loop;
        end if;
        set v_price = get_latest_price(v_ticker);
        insert into tmp_alerts
        values (v_user, v_ticker, v_target, v_price,
                if(v_price >= v_target, 'target reached', 'not yet'));
    end loop;
    close cur;

    select * from tmp_alerts;
end //

delimiter ;

call user_invest_report();
call check_target_alerts();


-- 1. read-only analyst: can only see the safe views, nothing else
create user 'analyst'@'localhost' identified by 'Analyst@123';
grant select on stockport.v_public_users to 'analyst'@'localhost';
grant select on stockport.v_sector_summary to 'analyst'@'localhost';

-- 2. app user: can read prices and add transactions only through the procedure
create user 'app_user'@'localhost' identified by 'AppUser@123';
grant select on stockport.assets to 'app_user'@'localhost';
grant select on stockport.daily_prices to 'app_user'@'localhost';
grant execute on procedure stockport.add_transaction to 'app_user'@'localhost';

-- check what each user has
show grants for 'analyst'@'localhost';
show grants for 'app_user'@'localhost';

-- take a privilege away
revoke select on stockport.v_sector_summary from 'analyst'@'localhost';
show grants for 'analyst'@'localhost';
