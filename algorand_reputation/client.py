"""Algorand algod and indexer client wrapper.

Provides input sanitization/validation, simple rate limiting, and retry/backoff
for resilient access to Algorand nodes (algod) and the indexer.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Final, Callable, TypeVar

from algosdk import encoding as algoenc
from algosdk.v2client import algod, indexer

T = TypeVar("T")

NETWORKS: Final = {
    "mainnet": {
        "algod": "https://mainnet-api.4160.nodely.dev",
        "indexer": "https://mainnet-idx.4160.nodely.dev",
    },
    "testnet": {
        "algod": "https://testnet-api.4160.nodely.dev",
        "indexer": "https://testnet-idx.4160.nodely.dev",
    },
}


class AlgorandClient:
    """Thin convenience wrapper around Algorand algod + indexer clients.

    Parameters
    ----------
    network_choice: str
        Either "mainnet" or "testnet" (default testnet if unknown)
    purestake_token: str | None
        API key/token. If None, tries env vars: ALGOD_API_KEY, PURESTAKE_API_KEY.
    rate_limit_per_sec: float | None
        Optional simple client-side rate limit (requests per second) shared across calls.
    max_retries: int
        Number of retries on transient failures (e.g., rate limit/timeout).
    backoff_factor: float
        Exponential backoff base delay in seconds.

    Environment variables (optional overrides)
    -----------------------------------------
    - ALGOREP_RATE_LIMIT_PER_SEC: float rate limit shared across calls
    - ALGOREP_MAX_RETRIES: int number of retry attempts
    - ALGOREP_BACKOFF_FACTOR: float backoff base delay seconds
    - ALGOREP_RETRY_JITTER: 1/true/yes/on to enable backoff jitter
    """

    def __init__(
        self,
        network_choice: str = "testnet",
        purestake_token: Optional[str] = None,
        rate_limit_per_sec: Optional[float] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        *,
        enable_jitter: bool | None = None,
    ) -> None:
        network_choice = network_choice.lower().strip()
        if network_choice not in NETWORKS:
            network_choice = "testnet"
        self.network_choice = network_choice

        # Env-driven toggles and overrides
        if enable_jitter is None:
            env_val = os.getenv("ALGOREP_RETRY_JITTER", "0").lower()
            enable_jitter = env_val in {"1", "true", "yes", "on"}
        self._enable_jitter = bool(enable_jitter)

        # Optional env overrides for rate limiting and retries
        env_rate = os.getenv("ALGOREP_RATE_LIMIT_PER_SEC")
        if env_rate is not None:
            try:
                rate_limit_per_sec = float(env_rate)
            except ValueError:
                pass
        env_retries = os.getenv("ALGOREP_MAX_RETRIES")
        if env_retries is not None:
            try:
                max_retries = int(env_retries)
            except ValueError:
                pass
        env_backoff = os.getenv("ALGOREP_BACKOFF_FACTOR")
        if env_backoff is not None:
            try:
                backoff_factor = float(env_backoff)
            except ValueError:
                pass

        token = (
            purestake_token
            or os.getenv("ALGOD_API_KEY")
            or os.getenv("PURESTAKE_API_KEY")
        )
        if not token:
            raise ValueError(
                (
                    "Missing PureStake / Nodely API token. Pass purestake_token or set "
                    "ALGOD_API_KEY/PURESTAKE_API_KEY env var."
                )
            )

        self.algod_address = NETWORKS[network_choice]["algod"]
        self.indexer_address = NETWORKS[network_choice]["indexer"]
        self.headers = {"X-API-Key": token}
        self.algod_client = algod.AlgodClient(token, self.algod_address, self.headers)
        self.indexer_client = indexer.IndexerClient(token, self.indexer_address, self.headers)
        self._log = logging.getLogger(__name__)

        # rate limiting
        self._rate_limit_per_sec = rate_limit_per_sec
        self._min_interval = 1.0 / rate_limit_per_sec if rate_limit_per_sec else 0.0
        self._last_call_time = 0.0

        # retries
        self._max_retries = max(0, int(max_retries))
        self._backoff_factor = max(0.0, float(backoff_factor))

    # --------------- internal helpers ---------------
    def _throttle(self) -> None:
        """Sleep just enough to honor the configured client-side rate limit."""
        if self._min_interval <= 0:
            return
        now = time.time()
        delta = now - self._last_call_time
        if delta < self._min_interval:
            sleep_for = self._min_interval - delta
            # low-volume debug log only when sleeping
            if sleep_for > 0:
                try:
                    self._log.debug("throttle: sleeping %.3fs", sleep_for)
                except Exception:
                    pass
                time.sleep(sleep_for)
        self._last_call_time = time.time()

    def _normalize_address(self, address: str) -> str:
        """Trim whitespace and normalize casing for downstream validation."""
        return (address or "").strip().upper()

    def _validate_address(self, address: str) -> str:
        """Normalize and validate an Algorand address or raise ValueError."""
        normalized = self._normalize_address(address)
        if not normalized or not algoenc.is_valid_address(normalized):
            raise ValueError(f"Invalid Algorand address: {address!r}")
        return normalized

    def _with_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute `func(*args, **kwargs)` with throttle and retry/backoff.

        Retries up to `_max_retries` with exponential backoff and optional jitter.
        """
        import random

        attempt = 0
        while True:
            try:
                self._throttle()
                return func(*args, **kwargs)
            except Exception:  # pragma: no cover - network behavior varies
                attempt += 1
                if attempt > self._max_retries:
                    raise
                # exponential backoff + optional jitter
                base_delay = self._backoff_factor * (2 ** (attempt - 1))
                jitter = random.uniform(0, base_delay / 2) if self._enable_jitter else 0.0
                time.sleep(base_delay + jitter)

    # --------------- public API ---------------
    def fetch_account_balance(self, account_address: str) -> Optional[float]:
        """Return account balance in ALGOs or None on error.

        Parameters
        ----------
        account_address: str
            Algorand address to query. Normalized and validated before use.

        Returns
        -------
        Optional[float]
            Account balance in ALGOs (not microalgos), or None on error.
        """
        try:
            addr = self._validate_address(account_address)
            account_info = self._with_retry(self.algod_client.account_info, addr)
            if isinstance(account_info, (bytes, bytearray)):
                import json
                account_info = json.loads(account_info)
            return account_info.get("amount", 0) / 1e6
        except Exception as e:  # pragma: no cover - network failures
            self._log.warning("Error fetching account balance: %s", e)
            return None

    def fetch_transactions(self, account_address: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch recent transactions for an address.

        Parameters
        ----------
        account_address: str
            Algorand address to query. Normalized and validated before use.
        limit: int
            Maximum number of transactions to return (client-side cap).
            Values <= 0 default to 1; values > 10000 clamp to 10000.

        Returns
        -------
        List[Dict[str, Any]]
            A list of indexer transaction dicts; empty list on failure.
        """
        try:
            addr = self._validate_address(account_address)
            safe_limit = 1 if limit <= 0 else min(int(limit), 10000)
            response = self._with_retry(
                self.indexer_client.search_transactions_by_address,
                addr,
                limit=safe_limit,
            )
            return response.get("transactions", [])
        except Exception as e:  # pragma: no cover
            self._log.warning("Error fetching transactions: %s", e)
            return []

    def fetch_asa_holdings(self, account_address: str) -> List[Dict[str, Any]]:
        """Return ASA (Algorand Standard Asset) holdings for an address.

        Parameters
        ----------
        account_address: str
            Algorand address to query. Normalized and validated before use.

        Returns
        -------
        List[Dict[str, Any]]
            A list of asset holding dicts; empty list on failure.
        """
        try:
            addr = self._validate_address(account_address)
            response = self._with_retry(self.indexer_client.lookup_account_assets, addr)
            return response.get("assets", [])
        except Exception as e:  # pragma: no cover
            self._log.warning("Error fetching ASA holdings: %s", e)
            return []

    def network(self) -> str:
        """Return network name (mainnet/testnet)."""
        return self.network_choice

__all__ = ["AlgorandClient"]
