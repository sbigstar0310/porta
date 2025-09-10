-- backend/schema.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT CURRENT_TIMESTAMP,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    language VARCHAR(2) NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    base_currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    cash DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id)
);

-- 트리거로 updated_at 자동 업데이트
CREATE TRIGGER IF NOT EXISTS portfolio_updated_at 
    AFTER UPDATE ON portfolios
BEGIN
    UPDATE portfolios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 거래 기록 테이블
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    transaction_type VARCHAR(4) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    shares DECIMAL(18,2) NOT NULL,
    price DECIMAL(18,2) NOT NULL,
    transaction_date DATE NOT NULL,
    fee DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    exchange VARCHAR(50) DEFAULT '',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- 현재 포지션 테이블 (집계 데이터)
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    total_shares DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    avg_buy_price DECIMAL(18,2) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, ticker)
);

-- 포지션 업데이트 트리거
CREATE TRIGGER IF NOT EXISTS position_updated_at 
    AFTER UPDATE ON positions
BEGIN
    UPDATE positions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_ticker 
    ON transactions(portfolio_id, ticker);
CREATE INDEX IF NOT EXISTS idx_transactions_date 
    ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio 
    ON positions(portfolio_id);

-- Dummy Data
-- 한국 사용자 (language: ko, timezone: Asia/Seoul)
INSERT OR IGNORE INTO users (id, email, timezone, language) 
VALUES (1, 'sbigstar0310@kaist.ac.kr', 'Asia/Seoul', 'ko');

-- 포트폴리오: 총 $25,000 (현금 $17,650 + 주식 $7,350) - 2024년 실제 주가 기반
INSERT OR IGNORE INTO portfolios (id, user_id, base_currency, cash) 
VALUES (1, 1, 'USD', 17650.00);

-- 거래 기록: 4개 종목, 2024년 실제 주가 기반 분산 매수
-- AAPL (총 8주, 평균 단가 $228.75) - 투자금액: $1,830 (7.3%)
INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'AAPL', 'BUY', 5.00, 225.50, '2024-10-15', 2.50, 'USD', 'NASDAQ', 'Initial AAPL position');

INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'AAPL', 'BUY', 3.00, 234.00, '2024-11-20', 1.95, 'USD', 'NASDAQ', 'AAPL DCA buy');

-- MSFT (총 4주, 평균 단가 $422.37) - 투자금액: $1,689 (6.8%)
INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'MSFT', 'BUY', 2.00, 420.00, '2024-10-01', 2.20, 'USD', 'NASDAQ', 'MSFT initial position');

INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'MSFT', 'BUY', 2.00, 424.74, '2024-10-24', 2.20, 'USD', 'NASDAQ', 'MSFT post-earnings');

-- GOOGL (총 15주, 평균 단가 $172.00) - 투자금액: $2,580 (10.3%)
INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'GOOGL', 'BUY', 8.00, 170.00, '2024-09-25', 2.25, 'USD', 'NASDAQ', 'GOOGL AI opportunity');

INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'GOOGL', 'BUY', 7.00, 174.50, '2024-11-05', 2.10, 'USD', 'NASDAQ', 'GOOGL cloud growth');

-- NVDA (총 10주, 평균 단가 $136.50) - 투자금액: $1,365 (5.5%)
INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'NVDA', 'BUY', 6.00, 135.00, '2024-10-30', 2.80, 'USD', 'NASDAQ', 'NVDA AI chip leader');

INSERT OR IGNORE INTO transactions (portfolio_id, ticker, transaction_type, shares, price, transaction_date, fee, currency, exchange, notes) 
VALUES (1, 'NVDA', 'BUY', 4.00, 139.00, '2024-11-15', 2.40, 'USD', 'NASDAQ', 'NVDA momentum');

-- 현재 포지션 (실제 거래 기반 가중평균 매수가)
INSERT OR IGNORE INTO positions (portfolio_id, ticker, total_shares, avg_buy_price) 
VALUES (1, 'AAPL', 8.00, 228.75);

INSERT OR IGNORE INTO positions (portfolio_id, ticker, total_shares, avg_buy_price) 
VALUES (1, 'MSFT', 4.00, 422.37);

INSERT OR IGNORE INTO positions (portfolio_id, ticker, total_shares, avg_buy_price) 
VALUES (1, 'GOOGL', 15.00, 172.00);

INSERT OR IGNORE INTO positions (portfolio_id, ticker, total_shares, avg_buy_price) 
VALUES (1, 'NVDA', 10.00, 136.50);