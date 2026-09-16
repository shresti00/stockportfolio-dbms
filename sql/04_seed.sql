DELETE FROM TRANSACTIONS;
DELETE FROM USERS;

INSERT INTO USERS (user_id, username) VALUES (1, 'dale_cooper');
INSERT INTO USERS (user_id, username) VALUES (2, 'laura_palmer');
INSERT INTO USERS (user_id, username) VALUES (3, 'bobby_briggs');

-- Dale Cooper's Portfolio 
INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (101, 1, 'AAPL', 'BUY', 15, 182.50, SYSDATE - 240);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (102, 1, 'MSFT', 'BUY', 8, 390.00, SYSDATE - 180);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (103, 1, 'NVDA', 'BUY', 20, 115.00, SYSDATE - 120);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (104, 1, 'GOOGL', 'BUY', 10, 145.25, SYSDATE - 90);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (105, 1, 'AAPL', 'BUY', 10, 169.00, SYSDATE - 30);

-- Laura Palmer's Portfolio
INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (201, 2, 'NVDA', 'BUY', 40, 108.00, SYSDATE - 200);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (202, 2, 'MSFT', 'BUY', 12, 402.50, SYSDATE - 75);

-- Bobby Briggs's Portfolio
INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (301, 3, 'GOOGL', 'BUY', 6, 150.00, SYSDATE - 60);

INSERT INTO TRANSACTIONS (transaction_id, user_id, ticker, txn_type, quantity, price_per_share, txn_date)
VALUES (302, 3, 'AAPL', 'BUY', 3, 175.50, SYSDATE - 15);

COMMIT;