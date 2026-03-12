// Initialize gloria_trade database with collections and indexes
db = db.getSiblingDB('gloria_trade');

// Create collections
db.createCollection('users');
db.createCollection('user_sessions');
db.createCollection('countries');
db.createCollection('exchanges');
db.createCollection('securities');
db.createCollection('corporate_actions');
db.createCollection('price_history_daily', {
  timeseries: {
    timeField: 'date',
    metaField: 'security_id',
    granularity: 'hours'
  }
});
db.createCollection('price_ticks_intraday', {
  timeseries: {
    timeField: 'timestamp',
    metaField: 'security_id',
    granularity: 'seconds'
  }
});
db.createCollection('portfolios');
db.createCollection('watchlists');
db.createCollection('orders');
db.createCollection('sentiment_records');
db.createCollection('ml_models');
db.createCollection('ml_predictions');
db.createCollection('system_config');

// Seed countries
db.countries.insertMany([
  {
    code: 'IN',
    name: 'India',
    default_currency: 'INR',
    regulatory_body: 'SEBI',
    market_timezone: 'Asia/Kolkata',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    code: 'US',
    name: 'United States',
    default_currency: 'USD',
    regulatory_body: 'SEC',
    market_timezone: 'America/New_York',
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  }
]);

// Seed exchanges
db.exchanges.insertMany([
  {
    code: 'BSE',
    name: 'Bombay Stock Exchange',
    mic_code: 'XBOM',
    country_code: 'IN',
    currency: 'INR',
    timezone: 'Asia/Kolkata',
    trading_days: [0, 1, 2, 3, 4],
    sessions: [
      { name: 'Pre-Open', open_time: '09:00', close_time: '09:15' },
      { name: 'Regular', open_time: '09:15', close_time: '15:30' },
      { name: 'Post-Close', open_time: '15:40', close_time: '16:00' }
    ],
    lot_size: 1,
    tick_size: 0.05,
    circuit_breaker_pct: 20.0,
    is_active: true,
    data_source: 'yahoo_finance',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    code: 'NSE',
    name: 'National Stock Exchange of India',
    mic_code: 'XNSE',
    country_code: 'IN',
    currency: 'INR',
    timezone: 'Asia/Kolkata',
    trading_days: [0, 1, 2, 3, 4],
    sessions: [
      { name: 'Pre-Open', open_time: '09:00', close_time: '09:15' },
      { name: 'Regular', open_time: '09:15', close_time: '15:30' },
      { name: 'Post-Close', open_time: '15:40', close_time: '16:00' }
    ],
    lot_size: 1,
    tick_size: 0.05,
    circuit_breaker_pct: 20.0,
    is_active: true,
    data_source: 'yahoo_finance',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    code: 'NASDAQ',
    name: 'NASDAQ Stock Market',
    mic_code: 'XNAS',
    country_code: 'US',
    currency: 'USD',
    timezone: 'America/New_York',
    trading_days: [0, 1, 2, 3, 4],
    sessions: [
      { name: 'Pre-Market', open_time: '04:00', close_time: '09:30' },
      { name: 'Regular', open_time: '09:30', close_time: '16:00' },
      { name: 'After-Hours', open_time: '16:00', close_time: '20:00' }
    ],
    lot_size: 1,
    tick_size: 0.01,
    is_active: true,
    data_source: 'yahoo_finance',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    code: 'NYSE',
    name: 'New York Stock Exchange',
    mic_code: 'XNYS',
    country_code: 'US',
    currency: 'USD',
    timezone: 'America/New_York',
    trading_days: [0, 1, 2, 3, 4],
    sessions: [
      { name: 'Pre-Market', open_time: '04:00', close_time: '09:30' },
      { name: 'Regular', open_time: '09:30', close_time: '16:00' },
      { name: 'After-Hours', open_time: '16:00', close_time: '20:00' }
    ],
    lot_size: 1,
    tick_size: 0.01,
    is_active: true,
    data_source: 'yahoo_finance',
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    code: 'AMEX',
    name: 'NYSE American (AMEX)',
    mic_code: 'XASE',
    country_code: 'US',
    currency: 'USD',
    timezone: 'America/New_York',
    trading_days: [0, 1, 2, 3, 4],
    sessions: [
      { name: 'Regular', open_time: '09:30', close_time: '16:00' }
    ],
    lot_size: 1,
    tick_size: 0.01,
    is_active: true,
    data_source: 'yahoo_finance',
    created_at: new Date(),
    updated_at: new Date()
  }
]);

// Seed system config
db.system_config.insertMany([
  {
    key: 'trading.default_profit_pct',
    value: 2.0,
    description: 'Default profit percentage threshold for auto-sell signals',
    category: 'trading',
    is_secret: false,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'trading.default_loss_pct',
    value: 2.0,
    description: 'Default loss percentage threshold for stop-loss signals',
    category: 'trading',
    is_secret: false,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'trading.default_simulation_ticks',
    value: 400,
    description: 'Number of ticks in day-trade simulation',
    category: 'trading',
    is_secret: false,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    key: 'ml.default_lookback_window',
    value: 60,
    description: 'Default LSTM lookback window in days',
    category: 'ml',
    is_secret: false,
    created_at: new Date(),
    updated_at: new Date()
  }
]);

print('Gloria-Trade database initialized successfully!');
