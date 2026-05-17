# Carbon & Cashmere Python SDK

Crypto intelligence API for autonomous agents — Python client for 70+ x402-paid endpoints.

## Install

```bash
pip install carbon-cashmere
```

Or from source:

```bash
git clone https://github.com/CarbonCashmere/carbon-cashmere-python
cd carbon-cashmere-python
pip install -e .
```

## Quick Start

### Free Tier (no auth)

```python
from carbon_cashmere import Client

client = Client()
prices = client.get_prices()            # top 10 coins
fear = client.get_fear_greed()          # sentiment index
```

### Authenticated ($9.99/mo API key)

```python
client = Client(api_key="cc_live_...")

# Technical analytics
rsi_macd = client.get_indicators("BTC", set="extended")

# Volatility + GARCH
vol = client.get_volatility("BTC")
garch = client.get_garch("BTC")

# Bundles (discounted)
ultimate = client.get_btc_ultimate()    # 11 analytics, 32% off
quant = client.get_quant_research_suite(base="BTC", quote="ETH")
```

### x402 Micropayments (pay-per-call)

```python
# Stub — requires x402-py integration for auto-payment
from carbon_cashmere import Client, PaymentRequired

client = Client()
try:
    data = client.get_signal("BTC")
except PaymentRequired as e:
    # e.payload contains x402 payment-required headers
    # Use x402-py SDK to sign + retry with payment header
    print(f"Pay {e.payload['api_key_price']} for access")
```

## Endpoint Coverage

**L1 On-Chain:**
- `get_btc_whales()`, `get_btc_fee_market()`, `get_btc_rbf_pulse()`
- `get_kaspa_dag_pulse()`, `get_kaspa_block_propagation()`, `get_kaspa_mining_economics()`
- `get_onchain_pulse_btc()`

**L2 Analytics:**
- Indicators: `get_indicators()`
- Anomaly: `get_anomaly()`
- Cross-sectional: `get_rotation()`, `get_relative_strength()`, `get_dispersion()`
- Derivatives: `get_derivatives_analytics()`
- Factor: `get_factor_analytics()`
- Volatility: `get_volatility()`, `get_garch()`, `get_vol_regime()`
- Trend: `get_hurst()`, `get_trend()`, `get_mean_reversion()`
- Pairs: `get_rolling_correlation()`, `get_beta_to_btc()`, `get_cointegration()`

**L3 Research (LLM):**
- `get_daily_report()`, `get_weekly_report()`, `get_research(coin)`

**L5 Transparency:**
- `get_proven_track_record()` — verifiable FTMO results (81.25% WR)
- `get_signal_accuracy()`, `get_model_performance()`

**Bundles (discounted):**
- `get_btc_ultimate()` (32% off)
- `get_quant_research_suite()` (23% off)
- `get_research_replica()` (20% off)
- `get_full_onchain()` (17% off)
- `get_ecosystem_watch()` (budget bundle)

**Events:**
- `get_events_recent()` — polling event feed (whale_tx, regime_change, funding_extreme, price_spike, anomaly_fired)

**Discovery:**
- `get_prices()` (free)
- `get_fear_greed()` (free)
- `list_endpoints()` — all 70+ endpoints + current pricing

## Error Handling

```python
from carbon_cashmere import (
    Client,
    PaymentRequired,
    AuthenticationFailed,
    CarbonCashmereError,
)

client = Client()
try:
    data = client.get_indicators("BTC")
except PaymentRequired as e:
    print(f"Need to pay: {e.payload}")
except AuthenticationFailed as e:
    print(f"Bad API key: {e}")
except CarbonCashmereError as e:
    print(f"API error: {e}")
```

## Configuration

```python
client = Client(
    api_key="cc_live_...",       # optional
    base_url="https://api.carbon-cashmere.de",  # override for staging
    timeout=30,                  # seconds
)
```

## Links

- API docs: https://api.carbon-cashmere.de/v1/endpoints
- MCP server: https://api.carbon-cashmere.de/mcp/
- Live track record: https://api.carbon-cashmere.de/v1/proven-track-record (x402 $0.50)

## License

MIT. See `LICENSE`.

## Disclaimer

All responses include `_meta.disclaimer = "Informational research data only — not investment advice."` Always verify data independently before any trading decision.
