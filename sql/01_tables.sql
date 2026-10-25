
create table users(
    user_id int primary key auto_increment,
    username varchar(20) unique not null,
    email varchar(250) unique,
    created_at date default (current_date),
    pwd_hash varchar(250) not null default '',
    is_active boolean not null default true,
    last_login datetime null,
    failed_attempts int not null default 0    
);


create table assets(
    ticker varchar(10) primary key,
    company_name varchar(100) not null,
    sector varchar(50),
    cap_category varchar(50),
    constraint chkcap check(cap_category in ('LARGE','MID','SMALL'))
);

create table daily_prices(
    ticker varchar(10),
    price_date date not null,
    close_price decimal(10,2) not null,
    constraint pk_daily_pr primary key(ticker,price_date),
    constraint fk_prices_asset foreign key(ticker) references assets(ticker)
);

create table transactions(
    transaction_id int primary key auto_increment,
    user_id int not null,
    ticker varchar(10) not null,
    txn_type varchar(10) not null,
    quantity decimal(10,2) not null,
    price_per_share decimal(10,2) not null,
    txn_date date default (current_date),
    constraint fk_txn_user foreign key (user_id) references users(user_id),
    constraint fk_txn_asset foreign key (ticker) references assets(ticker),
    constraint chk_txn_type check (txn_type in ('BUY','SELL'))

);

create table watchlist(
    watchlist_id int primary key auto_increment,
    user_id int not null,
    ticker varchar(10) not null,
    target_price decimal(10,2),
    added_date date default(current_date),
    constraint fk_watch_user foreign key(user_id) references users(user_id),
    constraint fk_watch_asset foreign key(ticker) references assets(ticker),
    constraint uq_watch unique(user_id, ticker)
);

create table company_investments(
    investor_ticker varchar(10),
    investee_ticker varchar(10),
    shares_held int,
    stake_prct decimal(5,2),
    as_of_date date,
    constraint pk_company primary key(investor_ticker,investee_ticker,as_of_date),
    constraint fk_ci_investor foreign key(investor_ticker) references assets(ticker),
    constraint fk_ci_investee foreign key(investee_ticker) references assets(ticker),
    constraint chk_ci_diff check(investor_ticker <> investee_ticker),
    constraint chk_ci_stakeprct check(stake_prct between 0 and 100)
);

create table fund_house(
    fund_house_id int primary key,
    fund_house_nm varchar(30) not null
    
);

create table scheme(
    scheme_id int primary key,
    fund_house_id int not null,
    scheme_nm varchar(100) not null,
    category varchar(40),
    risk_level varchar(40),
    nav decimal(10,4),
    min_investment decimal(12,2) not null,
    expense_ratio decimal(4,2),
    constraint fk_scheme_fund foreign key(fund_house_id) references fund_house(fund_house_id),
    constraint chk_scheme_category check(category in('LARGE_CAP','MID_CAP','SMALL_CAP','FLEXI')),
    constraint chk_scheme_risk check(risk_level in ('LOW','MODERATE','HIGH'))
);

create table scheme_holdings(
    scheme_id int,
    ticker varchar(10),
    weight_pct decimal(5,2),
    as_of_date date,
    constraint fk_sh_scheme_id foreign key(scheme_id) references scheme(scheme_id),
    constraint fk_sh_ticker foreign key(ticker) references assets(ticker),
    constraint pk_sh primary key(scheme_id,ticker,as_of_date)
);

create table user_scheme_investments(
    investment_id int primary key,
    user_id int not null,
    scheme_id int not null,
    amount decimal(13,2) not null,
    units decimal(14,4),
    nav_at_purchase decimal(10,4),
    start_date date,
    sip_amount decimal(13,2) default null,
    status varchar(20),
    constraint fk_usi_user foreign key(user_id) references users(user_id),
    constraint fk_usi_scheme foreign key(scheme_id) references scheme(scheme_id),
    constraint chk_usi check(status in ('ACTIVE','PAUSED','REDEEMED'))

);

create table scheme_nav_history(
    scheme_id int,
    nav_date date,
    nav decimal(10,4),
    constraint pk_snh primary key(scheme_id, nav_date),
    constraint fk_snh_scheme foreign key(scheme_id) references scheme(scheme_id)
);

