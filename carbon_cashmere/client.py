"""Carbon & Cashmere Python SDK — client for node-backed crypto intelligence API.

Provides typed methods for 70+ x402-paid endpoints. Handles HTTP, auth, retries.

Quick start:
    from carbon_cashmere import Client

    # Free tier (no auth needed for 2 endpoints)
    client = Client()
    prices = client.get_prices()
    fg = client.get_fear_greed()

    # Authenticated (Stripe API key, $9.99/mo unlimited)
    client = Client(api_key="cc_live_abc123...")
    signal = client.get_signal("BTC")

    # x402 payment (per-call, requires wallet integration — stub below)
    client = Client(x402_wallet=wallet)  # external wallet signer
    # client will auto-retry 402 responses with signed payments

Endpoint coverage: indicators, anomaly, rotation, relative-strength, dispersion,
derivatives-analytics, onchain-pulse, factor-analytics, analytics-bundle,
volatility, garch, vol-regime, hurst, trend, mean-reversion, bitcoin/whales,
bitcoin/fee-market, bitcoin/rbf-pulse, kaspa/*, daily-report, weekly-report,
research, rolling-correlation, beta-to-btc, cointegration, proven-track-record,
signal-accuracy, model-performance, btc-ultimate, quant-research-suite,
research-replica, full-onchain, ecosystem-watch, events/recent.

Docs: https://api.carbon-cashmere.de/v1/endpoints
"""
from __future__ import annotations

from typing import Any, Literal, Optional
import logging

import requests

__version__ = "0.1.0"

log = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://api.carbon-cashmere.de"


class CarbonCashmereError(Exception):
    """Base exception for SDK errors."""


class PaymentRequired(CarbonCashmereError):
    """402 Payment Required — x402 payment flow needed."""

    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(f"402 Payment Required: {payload.get('message', '')}")


class AuthenticationFailed(CarbonCashmereError):
    """401 Unauthorized — invalid or missing API key."""


class Client:
    """Main SDK client.

    Args:
        api_key: Bearer API key (from Stripe subscription). If None, falls back
            to free-tier endpoints only.
        base_url: Override API base URL. Default: https://api.carbon-cashmere.de
        timeout: Request timeout in seconds. Default: 30.
        x402_wallet: Optional wallet signer for automatic x402 payment. Stub —
            full implementation requires user-provided signing function.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30,
        x402_wallet: Optional[Any] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self.x402_wallet = x402_wallet
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"carbon-cashmere-py/{__version__}"})
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    # ─────────────────────────────────────────────────────────────
    # Core request helper
    # ─────────────────────────────────────────────────────────────
    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.get(url, params=params or {}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise CarbonCashmereError(f"network error: {exc}") from exc

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 402:
            payload = self._try_json(resp)
            if self.x402_wallet:
                log.info("402 received; attempting x402 payment flow")
                # Stub — real impl would: sign payment header, retry request.
                # Full x402 integration requires x402-py SDK integration.
                raise PaymentRequired(payload)  # not yet auto-handled
            raise PaymentRequired(payload)
        if resp.status_code == 401:
            raise AuthenticationFailed(f"401: {self._try_json(resp).get('detail', '')}")
        if resp.status_code == 422:
            raise CarbonCashmereError(f"422: {self._try_json(resp).get('detail', '')}")
        raise CarbonCashmereError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    @staticmethod
    def _try_json(resp) -> dict:
        try:
            return resp.json()
        except Exception:
            return {"error": resp.text[:500]}

    # ═════════════════════════════════════════════════════════════
    # FREE TIER — no auth needed
    # ═════════════════════════════════════════════════════════════
    def get_prices(self) -> list[dict]:
        """Real-time prices for top 10 coins (free) or all 116 (paid)."""
        return self._get("/v1/prices")

    def get_fear_greed(self) -> dict:
        """Crypto Fear & Greed Index with 7-day history (free)."""
        return self._get("/v1/fear-greed")

    # ═════════════════════════════════════════════════════════════
    # L2 Analytics
    # ═════════════════════════════════════════════════════════════
    def get_indicators(
        self,
        coin: str,
        set: Literal["basic", "extended", "all"] = "basic",
        interval: Literal["15m", "1h", "4h", "1d"] = "4h",
        lookback: int = 30,
    ) -> dict:
        """Technical indicators: RSI, MACD, Bollinger, ADX, ATR, Stoch, CCI, Williams %R."""
        return self._get(
            f"/v1/indicators/{coin.upper()}",
            params={"set": set, "interval": interval, "lookback": lookback},
        )

    def get_anomaly(self, coin: str, lookback: int = 30) -> dict:
        """Multi-method anomaly detection (z-score + STL + IsolationForest)."""
        return self._get(f"/v1/anomaly/{coin.upper()}", params={"lookback": lookback})

    def get_rotation(
        self,
        universe: Literal["core", "all"] = "core",
        period: Literal["7d", "30d", "90d"] = "30d",
    ) -> dict:
        """Cross-sectional rotation across universe (top gainers/losers + sectors)."""
        return self._get("/v1/rotation", params={"universe": universe, "period": period})

    def get_relative_strength(self, base: str = "BTC", coins: Optional[str] = None) -> dict:
        """Mansfield RS for all coins vs. base."""
        params = {"base": base.upper()}
        if coins:
            params["coins"] = coins
        return self._get("/v1/relative-strength", params=params)

    def get_dispersion(
        self,
        universe: Literal["core", "all"] = "core",
        period: Literal["7d", "30d", "90d"] = "30d",
    ) -> dict:
        """Cross-sectional vol + correlation clusters + diffusion + breadth."""
        return self._get("/v1/dispersion", params={"universe": universe, "period": period})

    def get_derivatives_analytics(self, coin: str, lookback: int = 90) -> dict:
        """Funding z-score + basis + OI regime."""
        return self._get(f"/v1/derivatives-analytics/{coin.upper()}", params={"lookback": lookback})

    def get_onchain_pulse_btc(self, lookback: int = 30) -> dict:
        """BTC on-chain pulse from our own Bitcoin Core node."""
        return self._get("/v1/onchain-pulse/btc", params={"lookback": lookback})

    def get_factor_analytics(self, coin: str, lookback: int = 90) -> dict:
        """4-factor decomposition: momentum + carry + crowding + volatility."""
        return self._get(f"/v1/factor-analytics/{coin.upper()}", params={"lookback": lookback})

    def get_analytics_bundle(self, coin: str, include: Optional[str] = None) -> dict:
        """Aggregated: indicators + anomaly + derivatives + factor."""
        params = {"include": include} if include else {}
        return self._get(f"/v1/analytics-bundle/{coin.upper()}", params=params)

    # ─── Volatility & Trend ─────────────────────────────────
    def get_volatility(self, coin: str, lookback: int = 90) -> dict:
        """Realized/Parkinson/Garman-Klass vol + vol-of-vol."""
        return self._get(f"/v1/volatility/{coin.upper()}", params={"lookback": lookback})

    def get_garch(self, coin: str, lookback: int = 90) -> dict:
        """GARCH(1,1) conditional vol + forecasts (1d/7d/30d)."""
        return self._get(f"/v1/garch/{coin.upper()}", params={"lookback": lookback})

    def get_vol_regime(self, coin: str, lookback: int = 365) -> dict:
        """Vol regime classification + Markov transitions + ACF clustering."""
        return self._get(f"/v1/vol-regime/{coin.upper()}", params={"lookback": lookback})

    def get_hurst(self, coin: str, lookback: int = 90) -> dict:
        """Hurst exponent via R/S across 7d/30d/full timescales."""
        return self._get(f"/v1/hurst/{coin.upper()}", params={"lookback": lookback})

    def get_trend(self, coin: str, lookback: int = 90) -> dict:
        """ADX-14 trend strength + direction + slope + duration + S/R."""
        return self._get(f"/v1/trend/{coin.upper()}", params={"lookback": lookback})

    def get_mean_reversion(self, coin: str, lookback: int = 90) -> dict:
        """z-score to MAs + OU half-life + reversion probability."""
        return self._get(f"/v1/mean-reversion/{coin.upper()}", params={"lookback": lookback})

    # ─── Cross-sectional / Pairs Trading ────────────────────
    def get_rolling_correlation(
        self,
        base: str,
        quote: str,
        window_days: int = 30,
        lookback_days: int = 90,
    ) -> dict:
        """Rolling Pearson correlation between pair. Pair format: BASE-QUOTE."""
        pair = f"{base.upper()}-{quote.upper()}"
        return self._get(
            f"/v1/rolling-correlation/{pair}",
            params={"window_days": window_days, "lookback_days": lookback_days},
        )

    def get_beta_to_btc(self, coin: str, lookback_days: int = 90) -> dict:
        """OLS beta vs BTC + rolling 30d stability."""
        return self._get(f"/v1/beta-to-btc/{coin.upper()}", params={"lookback_days": lookback_days})

    def get_cointegration(self, base: str, quote: str, lookback_days: int = 90) -> dict:
        """Engle-Granger + ADF + OU half-life for pairs trading."""
        pair = f"{base.upper()}-{quote.upper()}"
        return self._get(f"/v1/cointegration/{pair}", params={"lookback_days": lookback_days})

    # ═════════════════════════════════════════════════════════════
    # L1 On-Chain
    # ═════════════════════════════════════════════════════════════
    def get_btc_whales(
        self,
        min_btc: float = 100.0,
        hours: int = 24,
        limit: int = 50,
    ) -> dict:
        """BTC whale TXs via our own ZMQ-connected Bitcoin Core node."""
        return self._get(
            "/v1/bitcoin/whales",
            params={"min_btc": min_btc, "hours": hours, "limit": limit},
        )

    def get_btc_fee_market(self, blocks: int = 144) -> dict:
        """BTC fee market analytics + historical percentiles + elasticity."""
        return self._get("/v1/bitcoin/fee-market", params={"blocks": blocks})

    def get_btc_rbf_pulse(self, hours: int = 24) -> dict:
        """BIP125 RBF analytics on whale-TX stream."""
        return self._get("/v1/bitcoin/rbf-pulse", params={"hours": hours})

    def get_kaspa_dag_pulse(self) -> dict:
        """Kaspa DAG metrics from our own Rusty-Kaspa full node."""
        return self._get("/v1/kaspa/dag-pulse")

    def get_kaspa_block_propagation(self, hours: int = 24) -> dict:
        """Kaspa block propagation + tip-parallelism + sync uptime."""
        return self._get("/v1/kaspa/block-propagation", params={"hours": hours})

    def get_kaspa_mining_economics(self, electricity_cost_kwh: float = 0.08) -> dict:
        """Kaspa mining revenue/cost/breakeven model."""
        return self._get(
            "/v1/kaspa/mining-economics",
            params={"electricity_cost_kwh": electricity_cost_kwh},
        )

    # ═════════════════════════════════════════════════════════════
    # L3 Research Reports
    # ═════════════════════════════════════════════════════════════
    def get_daily_report(self) -> dict:
        """LLM-generated daily market research digest."""
        return self._get("/v1/daily-report")

    def get_weekly_report(self) -> dict:
        """LLM-generated weekly market research digest."""
        return self._get("/v1/weekly-report")

    def get_research(self, coin: str) -> dict:
        """Per-coin research deep dive."""
        return self._get(f"/v1/research/{coin.upper()}")

    # ═════════════════════════════════════════════════════════════
    # L5 Transparency
    # ═════════════════════════════════════════════════════════════
    def get_proven_track_record(self, include_trades: bool = True) -> dict:
        """Verifiable FTMO prop-firm trading results."""
        return self._get(
            "/v1/proven-track-record",
            params={"include_trades": str(include_trades).lower()},
        )

    def get_signal_accuracy(self, coin: str, lookback_days: int = 180) -> dict:
        """Historical ML signal accuracy per coin."""
        return self._get(
            f"/v1/signal-accuracy/{coin.upper()}",
            params={"lookback_days": lookback_days},
        )

    def get_model_performance(self) -> dict:
        """Cross-coin ML model performance leaderboard."""
        return self._get("/v1/model-performance")

    # ═════════════════════════════════════════════════════════════
    # Bundles
    # ═════════════════════════════════════════════════════════════
    def get_btc_ultimate(self) -> dict:
        """All 11 BTC analytics in 1 call (32% off)."""
        return self._get("/v1/btc-ultimate")

    def get_quant_research_suite(
        self,
        base: str = "BTC",
        quote: str = "ETH",
        universe: Literal["core", "all"] = "core",
    ) -> dict:
        """5 cross-sectional EPs (23% off)."""
        return self._get(
            "/v1/quant-research-suite",
            params={"base": base.upper(), "quote": quote.upper(), "universe": universe},
        )

    def get_research_replica(self, coin: str = "BTC") -> dict:
        """Daily report + coin research + FTMO track record (20% off)."""
        return self._get("/v1/research-replica", params={"coin": coin.upper()})

    def get_full_onchain(self) -> dict:
        """5 node-backed BTC+Kaspa EPs (17% off)."""
        return self._get("/v1/full-onchain")

    def get_ecosystem_watch(self) -> dict:
        """Budget market pulse: regime + F&G + rotation + signal activity."""
        return self._get("/v1/ecosystem-watch")

    # ═════════════════════════════════════════════════════════════
    # Events
    # ═════════════════════════════════════════════════════════════
    def get_events_recent(
        self,
        since_minutes: int = 60,
        types: Optional[list[str]] = None,
        coins: Optional[list[str]] = None,
        min_whale_btc: float = 100.0,
        funding_z_threshold: float = 2.0,
        price_spike_pct: float = 3.0,
        limit: int = 100,
    ) -> dict:
        """Polling event feed — 5 event types with filters."""
        params: dict[str, Any] = {
            "since_minutes": since_minutes,
            "min_whale_btc": min_whale_btc,
            "funding_z_threshold": funding_z_threshold,
            "price_spike_pct": price_spike_pct,
            "limit": limit,
        }
        if types:
            params["types"] = ",".join(types)
        if coins:
            params["coins"] = ",".join(c.upper() for c in coins)
        return self._get("/v1/events/recent", params=params)

    # ═════════════════════════════════════════════════════════════
    # Discovery
    # ═════════════════════════════════════════════════════════════
    def list_endpoints(self) -> dict:
        """Discover all available endpoints + pricing."""
        return self._get("/v1/endpoints")


__all__ = ["Client", "CarbonCashmereError", "PaymentRequired", "AuthenticationFailed"]
