
-- sector wise investment allocation
select a.sector, sum(t.quantity*t.price_per_share) as total_invested from transactions t
join assets a on t.ticker = a.ticker group by a.sector;


-- total amt invested per user
select u.username, sum(t.quantity*t.price_per_share) as total_invested from users u
join transactions t on u.user_id=t.user_id group by u.username;


-- which stock has most money invested init overall
select ticker, sum(quantity*price_per_share) as total_invested from transactions
group by ticker order by total_invested desc;


-- each user's current holdings(what tickers nd qnty)
select u.username, t.ticker, sum(t.quantity) as total_quantity
from users u
join transactions t on u.user_id = t.user_id
group by u.username, t.ticker;


-- watchlist of user
select u.username, w.ticker, w.target_price from watchlist w
join users u on w.user_id=u.user_id;