from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable


class ReputationScore:
    """Heuristic reputation scoring for Algorand accounts.

    Logic is intentionally simple & explainable. Not production risk analysis.
    """

    SIX_MONTHS_SECONDS = 60 * 60 * 24 * 30 * 6  # approximate

    def __init__(
        self,
        client: Any,
        *,
        recent_weight: int = 10,
        stale_weight: int = 5,
        pay_txn_multiplier: float = 1.0,
        asset_transfer_points: float = 10.0,
        app_call_points: float = 20.0,
        high_frequency_penalty_threshold: int = 1000,
        high_frequency_penalty: float = -10.0,
        normal_activity_reward: float = 10.0,
        inactivity_penalty: float = -10.0,
        asa_holding_multiplier: float = 0.1,
        normalization_cap: float = 100.0,
    ) -> None:
        self.client = client
        self.recent_weight = recent_weight
        self.stale_weight = stale_weight
        self.pay_txn_multiplier = pay_txn_multiplier
        self.asset_transfer_points = asset_transfer_points
        self.app_call_points = app_call_points
        self.high_frequency_penalty_threshold = high_frequency_penalty_threshold
        self.high_frequency_penalty = high_frequency_penalty
        self.normal_activity_reward = normal_activity_reward
        self.inactivity_penalty = inactivity_penalty
        self.asa_holding_multiplier = asa_holding_multiplier
        self.normalization_cap = normalization_cap

    def calculate_recency_weight(self, timestamp: int | float) -> int:
        now = datetime.now().timestamp()
        if now - float(timestamp) < self.SIX_MONTHS_SECONDS:
            return self.recent_weight
        return self.stale_weight

    def transaction_frequency_score(self, transactions: Iterable[Dict[str, Any]]) -> float:
        count = sum(1 for _ in transactions)
        if count > self.high_frequency_penalty_threshold:
            return self.high_frequency_penalty
        return self.normal_activity_reward if count > 0 else 0.0

    def apply_reputation_decay(self, last_timestamp: int | float) -> float:
        if not last_timestamp:
            return self.inactivity_penalty
        if datetime.now().timestamp() - float(last_timestamp) > self.SIX_MONTHS_SECONDS:
            return self.inactivity_penalty
        return 0.0

    def calculate_reputation(self, account_address: str) -> float:
        txns = list(self.client.fetch_transactions(account_address))
        if not txns:
            return 0.0
        score = 0.0
        last_ts = 0.0
        for txn in txns:
            ts = txn.get("round-time") or txn.get("roundTime") or 0
            weight = self.calculate_recency_weight(ts)
            tx_type = txn.get("tx-type") or txn.get("txType")
            if tx_type == "pay":
                amt = (txn.get("payment-transaction") or {}).get("amount", 0) / 1e6
                score += amt * weight * self.pay_txn_multiplier
            elif tx_type == "axfer":
                score += self.asset_transfer_points * weight
            elif tx_type == "appl":
                score += self.app_call_points
            if ts:
                last_ts = max(last_ts, float(ts))
        score += self.transaction_frequency_score(txns)
        score += self.apply_reputation_decay(last_ts)
        return score

    def normalize_score(self, raw: float) -> float:
        if self.normalization_cap <= 0:
            return 0.0
        return round(min((raw / self.normalization_cap) * 100.0, 100.0), 2)

    def get_reputation_score(self, account_address: str) -> float:
        raw = self.calculate_reputation(account_address)
        for asset in self.client.fetch_asa_holdings(account_address):
            raw += (asset.get("amount", 0) / 1e6) * self.asa_holding_multiplier
        return self.normalize_score(raw)

__all__ = ["ReputationScore"]
