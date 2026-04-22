"""Example usage of Carbon & Cashmere SDK — demonstrates free-tier + authenticated flows.

Run:
    export CC_API_KEY=cc_live_abc123
    python examples/quickstart.py
"""
import json
import os
import sys

# When running from sdk/python/ during development:
# sys.path.insert(0, ".")
from carbon_cashmere import Client, PaymentRequired


def demo_free_tier():
    """Free endpoints — no auth required."""
    client = Client()

    print("=== /v1/prices (free, top 10) ===")
    prices = client.get_prices()
    for p in prices[:5]:
        print(f"  {p['symbol']}: ${p['price_usd']:,.2f} ({p['change_24h']:+.2f}%)")

    print("\n=== /v1/fear-greed (free) ===")
    fg = client.get_fear_greed()
    print(json.dumps(fg, indent=2)[:300])


def demo_authenticated():
    """Authenticated endpoints — requires CC_API_KEY env var."""
    api_key = os.environ.get("CC_API_KEY")
    if not api_key:
        print("\n[skipped] Set CC_API_KEY env var for authenticated demo")
        return

    client = Client(api_key=api_key)

    print("\n=== /v1/indicators/BTC (basic set) ===")
    ind = client.get_indicators("BTC", set="basic")
    print(f"  RSI(14): {ind['indicators']['rsi_14']:.2f}")
    print(f"  MACD: {ind['indicators']['macd']['line']:.2f}")

    print("\n=== /v1/btc-ultimate (32% off, 11 analytics in 1 call) ===")
    bundle = client.get_btc_ultimate()
    pricing = bundle["pricing"]
    print(f"  Paid: ${pricing['bundle_price_usd']} "
          f"(saved ${pricing['separate_components_sum_usd'] - pricing['bundle_price_usd']:.2f})")
    components = bundle["components"]
    print(f"  Components delivered: {[k for k, v in components.items() if v is not None]}")

    print("\n=== /v1/proven-track-record (verifiable FTMO) ===")
    tr = client.get_proven_track_record(include_trades=False)
    s = tr["trade_statistics"]
    print(f"  Status: {tr['challenge']['status']}")
    print(f"  Return: +{tr['challenge']['pct_return']:.2f}% in {tr['challenge']['challenge_duration_days']} days")
    print(f"  WR: {s['win_rate']*100:.2f}% ({s['wins']}W/{s['losses']}L)")
    print(f"  Profit Factor: {s['profit_factor']}")


def demo_x402_stub():
    """x402 payment flow — currently a stub."""
    print("\n=== x402 payment stub ===")
    client = Client()  # no api_key
    try:
        _ = client.get_signal_accuracy("BTC")
    except PaymentRequired as e:
        print(f"  402 received: {e.payload.get('teaser', '(no teaser)')[:80]}")
        print(f"  Price: {e.payload.get('hint', '')[:80]}")
        print("  → Full x402 payment auto-retry requires x402-py integration")


if __name__ == "__main__":
    demo_free_tier()
    demo_authenticated()
    demo_x402_stub()
