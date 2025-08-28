"""Algorand algod and indexer client wrapper.

Provides input sanitization/validation, simple rate limiting, and retry/backoff
for resilient access to Algorand nodes (algod) and the indexer.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Final

from algosdk import encoding as algoenc
from algosdk.v2client import algod, indexer

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
    """

    def __init__(
        self,
        network_choice: str = "testnet",
        purestake_token: Optional[str] = None,
        rate_limit_per_sec: Optional[float] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        network_choice = network_choice.lower().strip()
        if network_choice not in NETWORKS:
            network_choice = "testnet"
        self.network_choice = network_choice

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

        # rate limiting
        self._rate_limit_per_sec = rate_limit_per_sec
        self._min_interval = 1.0 / rate_limit_per_sec if rate_limit_per_sec else 0.0
        self._last_call_time = 0.0

        # retries
        self._max_retries = max(0, int(max_retries))
        self._backoff_factor = max(0.0, float(backoff_factor))

    # --------------- internal helpers ---------------
    def _throttle(self) -> None:
        if self._min_interval <= 0:
            return
        now = time.time()
        delta = now - self._last_call_time
        if delta < self._min_interval:
            time.sleep(self._min_interval - delta)
        self._last_call_time = time.time()

    def _normalize_address(self, address: str) -> str:
        """Trim and normalize address casing for validation."""
        return (address or "").strip().upper()

    def _validate_address(self, address: str) -> str:
        """Normalize and validate an Algorand address or raise ValueError."""
        normalized = self._normalize_address(address)
        if not normalized or not algoenc.is_valid_address(normalized):
            raise ValueError(f"Invalid Algorand address: {address!r}")
        return normalized

    def _with_retry(self, func, *args, **kwargs):
        """Execute a callable with throttle and retry/backoff on transient errors."""
        attempt = 0
        while True:
            try:
                self._throttle()
                return func(*args, **kwargs)
            except Exception:  # pragma: no cover - network behavior varies
                attempt += 1
                if attempt > self._max_retries:
                    raise
                # exponential backoff
                delay = self._backoff_factor * (2 ** (attempt - 1))
                time.sleep(delay)

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
            return account_info.get("amount", 0) / 1e6
        except Exception as e:  # pragma: no cover - network failures
            print(f"[algorand_reputation] Error fetching account balance: {e}")
            return None

    def fetch_transactions(self, account_address: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch recent transactions for an address.

        Parameters
        ----------
        account_address: str
            Algorand address to query. Normalized and validated before use.
        limit: int
            Maximum number of transactions to return (client-side cap).

        Returns
        -------
        List[Dict[str, Any]]
            A list of indexer transaction dicts; empty list on failure.
        """
        try:
            addr = self._validate_address(account_address)
            response = self._with_retry(
                self.indexer_client.search_transactions_by_address,
                addr,
                limit=limit,
            )
            return response.get("transactions", [])
        except Exception as e:  # pragma: no cover
            print(f"[algorand_reputation] Error fetching transactions: {e}")
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
            print(f"[algorand_reputation] Error fetching ASA holdings: {e}")
            return []

    def network(self) -> str:
        """Return network name (mainnet/testnet)."""
        return self.network_choice

__all__ = ["AlgorandClient"]
