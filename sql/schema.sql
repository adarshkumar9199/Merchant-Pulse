-- Database Schema for Merchant Growth & Retention Decision Engine

-- 1. Merchants Table
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id VARCHAR(20) PRIMARY KEY,
    merchant_name VARCHAR(150) NOT NULL,
    merchant_category VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    onboarding_date DATE NOT NULL
);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(20) PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    device_type VARCHAR(20) NOT NULL,
    signup_date DATE NOT NULL
);

-- 3. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(30) PRIMARY KEY,
    merchant_id VARCHAR(20) NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    transaction_amount DECIMAL(12, 2) NOT NULL,
    transaction_status VARCHAR(20) NOT NULL,
    payment_type VARCHAR(30) NOT NULL,
    failure_reason VARCHAR(50) NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Indexes for high-performance analytical queries
CREATE INDEX IF NOT EXISTS idx_txn_merchant ON transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_txn_merchant_date ON transactions(merchant_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_merchant_city_cat ON merchants(city, merchant_category);
