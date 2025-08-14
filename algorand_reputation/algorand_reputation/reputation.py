from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable


class ReputationScore:
    """Heuristic reputation scoring for Algorand accounts.

    Logic intentionally simple & explainable. Weights can be tweaked via kwargs.
    Not for production risk assessment without further validation.
    """

    SIX_MONTHS_SECONDS = 60 * 60 * 24 * 30 * 6  # approx

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

    # ------------ component scores ------------
    def calculate_recency_weight(self, timestamp: int | float) -> int:
        current_time = datetime.now().timestamp()
        time_diff = current_time - float(timestamp)
        return self.recent_weight if time_diff < self.SIX_MONTHS_SECONDS else self.stale_weight

    def transaction_frequency_score(self, transactions: Iterable[Dict[str, Any]]) -> float:
        count = sum(1 for _ in transactions)
        # Rough yearly normalization heuristic (avoid division by zero)
        if count > self.high_frequency_penalty_threshold:
            return self.high_frequency_penalty
        return self.normal_activity_reward if count > 0 else 0.0

    def apply_reputation_decay(self, last_transaction_time: int | float) -> float:
        if not last_transaction_time:
            return self.inactivity_penalty  # never transacted
        current_time = datetime.now().timestamp()
        inactivity_period = current_time - float(last_transaction_time)
        if inactivity_period > self.SIX_MONTHS_SECONDS:
            return self.inactivity_penalty
        return 0.0

    # ------------ main scoring ------------
    def calculate_reputation(self, account_address: str) -> float:
        transactions = list(self.client.fetch_transactions(account_address))
        if not transactions:
            return 0.0

        score = 0.0
        last_transaction_time = 0.0

        for txn in transactions:
            ts = txn.get("round-time") or txn.get("roundTime") or 0
            recency_weight = self.calculate_recency_weight(ts)
            tx_type = txn.get("tx-type") or txn.get("txType")

            if tx_type == "pay":  # Payment
                payment = txn.get("payment-transaction") or {}
                amount_sent = payment.get("amount", 0) / 1e6
                score += amount_sent * recency_weight * self.pay_txn_multiplier
            elif tx_type == "axfer":  # Asset transfer
                score += self.asset_transfer_points * recency_weight
            elif tx_type == "appl":  # App call / smart contract
                score += self.app_call_points

            if ts:
                last_transaction_time = max(last_transaction_time, float(ts))

        score += self.transaction_frequency_score(transactions)
        score += self.apply_reputation_decay(last_transaction_time)
        return score

    def normalize_score(self, raw_score: float) -> float:
        if self.normalization_cap <= 0:
            return 0.0
        normalized_score = min((raw_score / self.normalization_cap) * 100.0, 100.0)
        return round(normalized_score, 2)

    def get_reputation_score(self, account_address: str) -> float:
        raw_score = self.calculate_reputation(account_address)
        assets = self.client.fetch_asa_holdings(account_address)
        for asset in assets:
            raw_score += (asset.get("amount", 0) / 1e6) * self.asa_holding_multiplier
        return self.normalize_score(raw_score)

__all__ = ["ReputationScore"]
