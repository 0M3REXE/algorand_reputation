"""Reputation scoring logic for Algorand accounts.

Implements explainable heuristics with enhanced pattern analysis, frequency,
recency weighting, inactivity decay, ASA holding influence, and normalization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Final, Iterable


class ReputationScore:
    """Enhanced heuristic reputation scoring for Algorand accounts.

    This class provides comprehensive reputation analysis with advanced features:
    - Multi-transaction type support (pay, axfer, appl, acfg, afrz, keyreg)
    - Pattern analysis including receiver diversity and transaction volumes
    - Large transaction bonuses and frequency analysis
    - Detailed score breakdowns and batch processing
    - Export capabilities and comparative analysis

    Logic is intentionally simple & explainable. Not production risk analysis.
    """

    SIX_MONTHS_SECONDS: Final = 60 * 60 * 24 * 30 * 6  # approximate

    def __init__(
        self,
        client: Any,
        *,
        recent_weight: int = 10,
        stale_weight: int = 5,
        pay_txn_multiplier: float = 1.0,
        asset_transfer_points: float = 10.0,
        app_call_points: float = 20.0,
        asset_config_points: float = 15.0,
        asset_freeze_points: float = 5.0,
        keyreg_points: float = 25.0,
        high_frequency_penalty_threshold: int = 1000,
        high_frequency_penalty: float = -10.0,
        normal_activity_reward: float = 10.0,
        inactivity_penalty: float = -10.0,
        asa_holding_multiplier: float = 0.1,
        normalization_cap: float = 100.0,
        large_transaction_bonus: float = 1.5,
        large_transaction_threshold: float = 10.0,
        receiver_diversity_bonus: float = 5.0,
        min_unique_receivers: int = 3,
    ) -> None:
        self.client = client
        self.recent_weight = recent_weight
        self.stale_weight = stale_weight
        self.pay_txn_multiplier = pay_txn_multiplier
        self.asset_transfer_points = asset_transfer_points
        self.app_call_points = app_call_points
        self.asset_config_points = asset_config_points
        self.asset_freeze_points = asset_freeze_points
        self.keyreg_points = keyreg_points
        self.high_frequency_penalty_threshold = high_frequency_penalty_threshold
        self.high_frequency_penalty = high_frequency_penalty
        self.normal_activity_reward = normal_activity_reward
        self.inactivity_penalty = inactivity_penalty
        self.asa_holding_multiplier = asa_holding_multiplier
        self.normalization_cap = normalization_cap
        self.large_transaction_bonus = large_transaction_bonus
        self.large_transaction_threshold = large_transaction_threshold
        self.receiver_diversity_bonus = receiver_diversity_bonus
        self.min_unique_receivers = min_unique_receivers

    def calculate_recency_weight(self, timestamp: int | float) -> int:
        now = datetime.now().timestamp()
        if now - float(timestamp) < self.SIX_MONTHS_SECONDS:
            return self.recent_weight
        return self.stale_weight

    def analyze_transaction_patterns(
        self, transactions: Iterable[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for advanced scoring.

        Returns a dict with keys: unique_receivers, total_volume,
        avg_transaction_size, transaction_types, receiver_diversity_score.
        """
        txn_list = list(transactions)
        if not txn_list:
            return {
                "unique_receivers": 0,
                "total_volume": 0.0,
                "avg_transaction_size": 0.0,
                "transaction_types": {},
                "receiver_diversity_score": 0.0
            }

        receivers = set()
        total_volume = 0.0
        transaction_types: Dict[str, int] = {}

        for txn in txn_list:
            tx_type = txn.get("tx-type") or txn.get("txType", "unknown")
            transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1

            # Track receivers for diversity analysis
            if tx_type == "pay":
                receiver = txn.get("payment-transaction", {}).get("receiver")
                if receiver:
                    receivers.add(receiver)
                    amount = txn.get("payment-transaction", {}).get("amount", 0) / 1e6
                    total_volume += amount
            elif tx_type == "axfer":
                receiver = txn.get("asset-transfer-transaction", {}).get("receiver")
                if receiver:
                    receivers.add(receiver)

        avg_transaction_size = total_volume / len(txn_list) if txn_list else 0.0
        diversity_ratio = len(receivers) / self.min_unique_receivers
        receiver_diversity_score = min(diversity_ratio, 1.0) * self.receiver_diversity_bonus

        return {
            "unique_receivers": len(receivers),
            "total_volume": total_volume,
            "avg_transaction_size": avg_transaction_size,
            "transaction_types": transaction_types,
            "receiver_diversity_score": receiver_diversity_score
        }

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
        """Calculate raw reputation score for an address.

        Aggregates per-transaction scores (type × recency), applies pattern
        bonuses/penalties, frequency reward/penalty, and inactivity decay.

        Returns the raw (non-normalized) score; use `get_reputation_score`
        to get a 0–100 normalized value.
        """
        txns = list(self.client.fetch_transactions(account_address))
        if not txns:
            return 0.0
        
        # Analyze transaction patterns
        pattern_analysis = self.analyze_transaction_patterns(txns)
        
        score = 0.0
        last_ts = 0.0
        
        # Calculate score for each transaction
        for txn in txns:
            score += self.calculate_transaction_score(txn)
            ts = txn.get("round-time") or txn.get("roundTime") or 0
            if ts:
                last_ts = max(last_ts, float(ts))
        
        # Add pattern-based bonuses
        score += pattern_analysis["receiver_diversity_score"]
        
        # Add frequency and activity bonuses
        score += self.transaction_frequency_score(txns)
        score += self.apply_reputation_decay(last_ts)
        
        return score

    def normalize_score(self, raw: float) -> float:
        """Normalize a raw score into [0, 100].

        If `normalization_cap` is 0 or negative, returns 0.0.
        The result is rounded to 2 decimal places.
        """
        if self.normalization_cap <= 0:
            return 0.0
        return round(min((raw / self.normalization_cap) * 100.0, 100.0), 2)

    def calculate_transaction_score(self, txn: Dict[str, Any]) -> float:
        """Calculate score for a single transaction with enhanced logic.

        Supports tx types: pay, axfer, appl, acfg, afrz, keyreg.
        """
        ts = txn.get("round-time") or txn.get("roundTime") or 0
        weight = self.calculate_recency_weight(ts)
        tx_type = txn.get("tx-type") or txn.get("txType")

        base_score = 0.0

        if tx_type == "pay":
            amt = (txn.get("payment-transaction") or {}).get("amount", 0) / 1e6
            base_score = amt * weight * self.pay_txn_multiplier

            # Large transaction bonus
            if amt >= self.large_transaction_threshold:
                base_score *= self.large_transaction_bonus

        elif tx_type == "axfer":
            base_score = self.asset_transfer_points * weight
        elif tx_type == "appl":
            base_score = self.app_call_points
        elif tx_type == "acfg":
            base_score = self.asset_config_points * weight
        elif tx_type == "afrz":
            base_score = self.asset_freeze_points * weight
        elif tx_type == "keyreg":
            base_score = self.keyreg_points * weight

        return base_score

    def get_reputation_score(self, account_address: str) -> float:
        """Compute final normalized reputation score for an address.

        Adds ASA holding contribution to the raw score from
        `calculate_reputation` and then normalizes to 0–100.
        """
        raw = self.calculate_reputation(account_address)
        for asset in self.client.fetch_asa_holdings(account_address):
            raw += (asset.get("amount", 0) / 1e6) * self.asa_holding_multiplier
        return self.normalize_score(raw)

    def get_detailed_reputation(
        self, account_address: str
    ) -> Dict[str, Any]:
        """Get detailed reputation analysis with breakdown."""
        txns = list(self.client.fetch_transactions(account_address))
        asa_holdings = list(self.client.fetch_asa_holdings(account_address))

        if not txns:
            return {
                "reputation_score": 0.0,
                "raw_score": 0.0,
                "breakdown": {
                    "transaction_score": 0.0,
                    "frequency_score": 0.0,
                    "decay_score": 0.0,
                    "asa_holding_score": 0.0,
                    "pattern_bonuses": 0.0
                },
                "analysis": {
                    "total_transactions": 0,
                    "unique_receivers": 0,
                    "total_volume": 0.0,
                    "asa_holdings_count": len(asa_holdings)
                }
            }

        # Calculate individual components
        pattern_analysis = self.analyze_transaction_patterns(txns)

        transaction_score = 0.0
        last_ts = 0.0

        for txn in txns:
            transaction_score += self.calculate_transaction_score(txn)
            ts = txn.get("round-time") or txn.get("roundTime") or 0
            if ts:
                last_ts = max(last_ts, float(ts))

        frequency_score = self.transaction_frequency_score(txns)
        decay_score = self.apply_reputation_decay(last_ts)
        pattern_bonuses = pattern_analysis["receiver_diversity_score"]

        asa_holding_score = sum(
            (asset.get("amount", 0) / 1e6) * self.asa_holding_multiplier
            for asset in asa_holdings
        )

        raw_score = (
            transaction_score + frequency_score + decay_score +
            pattern_bonuses + asa_holding_score
        )

        return {
            "reputation_score": self.normalize_score(raw_score),
            "raw_score": raw_score,
            "breakdown": {
                "transaction_score": transaction_score,
                "frequency_score": frequency_score,
                "decay_score": decay_score,
                "asa_holding_score": asa_holding_score,
                "pattern_bonuses": pattern_bonuses
            },
            "analysis": {
                "total_transactions": len(txns),
                "unique_receivers": pattern_analysis["unique_receivers"],
                "total_volume": pattern_analysis["total_volume"],
                "avg_transaction_size": pattern_analysis["avg_transaction_size"],
                "transaction_types": pattern_analysis["transaction_types"],
                "asa_holdings_count": len(asa_holdings)
            }
        }

    def get_batch_reputation_scores(
        self, account_addresses: list[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get reputation scores for multiple addresses efficiently."""
        results = {}

        for address in account_addresses:
            try:
                results[address] = self.get_detailed_reputation(address)
            except Exception as e:
                results[address] = {
                    "error": str(e),
                    "reputation_score": 0.0
                }

        return results

    def compare_accounts(
        self, account_addresses: list[str]
    ) -> Dict[str, Any]:
        """Compare multiple accounts and provide ranking."""
        batch_results = self.get_batch_reputation_scores(account_addresses)

        # Filter out errors and sort by score
        valid_results = {
            addr: data for addr, data in batch_results.items()
            if "error" not in data
        }

        sorted_accounts = sorted(
            valid_results.items(),
            key=lambda x: x[1]["reputation_score"],
            reverse=True
        )

        return {
            "ranking": [
                {
                    "address": addr,
                    "score": data["reputation_score"],
                    "rank": i + 1
                }
                for i, (addr, data) in enumerate(sorted_accounts)
            ],
            "summary": {
                "total_accounts": len(account_addresses),
                "valid_accounts": len(valid_results),
                "errors": len(batch_results) - len(valid_results),
                "highest_score": (
                    sorted_accounts[0][1]["reputation_score"]
                    if sorted_accounts else 0.0
                ),
                "lowest_score": (
                    sorted_accounts[-1][1]["reputation_score"]
                    if sorted_accounts else 0.0
                ),
                "average_score": (
                    sum(data["reputation_score"] for data in valid_results.values())
                    / len(valid_results) if valid_results else 0.0
                )
            },
            "detailed_results": batch_results
        }

    def export_reputation_data(
        self,
        account_addresses: list[str],
        format: str = "json"
    ) -> str:
        """Export reputation data in various formats."""
        comparison_data = self.compare_accounts(account_addresses)

        if format.lower() == "json":
            import json
            return json.dumps(comparison_data, indent=2)

        elif format.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "Address", "Score", "Rank", "Total Transactions",
                "Unique Receivers", "Total Volume", "ASA Holdings"
            ])

            # Write data
            for item in comparison_data["ranking"]:
                addr = item["address"]
                detailed = comparison_data["detailed_results"][addr]

                if "error" not in detailed:
                    analysis = detailed["analysis"]
                    writer.writerow([
                        addr,
                        item["score"],
                        item["rank"],
                        analysis["total_transactions"],
                        analysis["unique_receivers"],
                        analysis["total_volume"],
                        analysis["asa_holdings_count"]
                    ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'.")

    def get_reputation_insights(
        self,
        account_addresses: list[str]
    ) -> Dict[str, Any]:
        """Generate insights about reputation patterns across accounts."""
        comparison_data = self.compare_accounts(account_addresses)
        detailed_results = comparison_data["detailed_results"]

        # Analyze transaction type distribution
        txn_type_totals: Dict[str, int] = {}
        total_accounts = 0
        accounts_with_high_scores = 0
        high_score_threshold = 70.0

        for addr, data in detailed_results.items():
            if "error" in data:
                continue

            total_accounts += 1
            if data["reputation_score"] >= high_score_threshold:
                accounts_with_high_scores += 1

            # Aggregate transaction types
            for tx_type, count in data["analysis"]["transaction_types"].items():
                txn_type_totals[tx_type] = txn_type_totals.get(tx_type, 0) + count

        # Find most common transaction type
        most_common_txn = None
        if txn_type_totals:
            most_common_txn = max(
                txn_type_totals.items(),
                key=lambda x: x[1]
            )[0]

        return {
            "total_accounts_analyzed": total_accounts,
            "high_score_accounts": accounts_with_high_scores,
            "high_score_percentage": (
                (accounts_with_high_scores / total_accounts * 100)
                if total_accounts > 0 else 0.0
            ),
            "transaction_type_distribution": txn_type_totals,
            "most_common_txn_type": most_common_txn,
            "score_distribution": {
                "excellent": len([
                    d for d in detailed_results.values()
                    if d.get("reputation_score", 0) >= 90
                ]),
                "good": len([
                    d for d in detailed_results.values()
                    if 70 <= d.get("reputation_score", 0) < 90
                ]),
                "fair": len([
                    d for d in detailed_results.values()
                    if 50 <= d.get("reputation_score", 0) < 70
                ]),
                "poor": len([
                    d for d in detailed_results.values()
                    if d.get("reputation_score", 0) < 50
                ])
            }
        }
