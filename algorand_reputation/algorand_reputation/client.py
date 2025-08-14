from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
from algosdk.v2client import algod, indexer

NETWORKS = {
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
        Optional simple client‑side rate limit (requests per second) shared across calls.
    """

    def __init__(
        self,
        network_choice: str = "testnet",
        purestake_token: Optional[str] = None,
        rate_limit_per_sec: Optional[float] = None,
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
                "Missing PureStake / Nodely API token. Pass purestake_token or set ALGOD_API_KEY/PURESTAKE_API_KEY env var."
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

    # --------------- internal helpers ---------------
    def _throttle(self) -> None:
        if self._min_interval <= 0:
            return
        now = time.time()
        delta = now - self._last_call_time
        if delta < self._min_interval:
            time.sleep(self._min_interval - delta)
        self._last_call_time = time.time()

    # --------------- public API ---------------
    def fetch_account_balance(self, account_address: str) -> Optional[float]:
        """Return account balance in ALGOs or None on error."""
        try:
            self._throttle()
            account_info = self.algod_client.account_info(account_address)
            return account_info.get("amount", 0) / 1e6
        except Exception as e:  # pragma: no cover - network failures
            print(f"[algorand_reputation] Error fetching account balance: {e}")
            return None

    def fetch_transactions(self, account_address: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch recent transactions for an address.

        Returns empty list on failure. Limit parameter caps result size (indexer may page beyond but we keep simple).
        """
        try:
            self._throttle()
            response = self.indexer_client.search_transactions_by_address(
                account_address, limit=limit
            )
            return response.get("transactions", [])
        except Exception as e:  # pragma: no cover
            print(f"[algorand_reputation] Error fetching transactions: {e}")
            return []

    def fetch_asa_holdings(self, account_address: str) -> List[Dict[str, Any]]:
        """Return ASA (Algorand Standard Asset) holdings for an address.

        Empty list on failure.
        """
        try:
            self._throttle()
            response = self.indexer_client.lookup_account_assets(account_address)
            return response.get("assets", [])
        except Exception as e:  # pragma: no cover
            print(f"[algorand_reputation] Error fetching ASA holdings: {e}")
            return []

    def network(self) -> str:
        """Return network name (mainnet/testnet)."""
        return self.network_choice

__all__ = ["AlgorandClient"]
