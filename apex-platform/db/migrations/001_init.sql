-- Apex Commerce: initial schema migration
-- Migration: 001_init

CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(36) PRIMARY KEY,
    order_id   VARCHAR(36) NOT NULL,
    amount_cents BIGINT NOT NULL,
    currency   VARCHAR(3) NOT NULL DEFAULT 'USD',
    method     VARCHAR(32) NOT NULL,
    status     VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(status);

CREATE TABLE IF NOT EXISTS orders (
    order_id    VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,
    total_cents BIGINT NOT NULL,
    status      VARCHAR(32) NOT NULL DEFAULT 'pending',
    placed_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
