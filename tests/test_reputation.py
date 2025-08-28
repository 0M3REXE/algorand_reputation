"""Unit tests for ReputationScore."""

from datetime import datetime
from unittest.mock import Mock
from algorand_reputation.reputation import ReputationScore

VALID_ADDR = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
"""Unit tests for ReputationScore."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from algorand_reputation.reputation import ReputationScore

VALID_ADDR = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"


class TestReputationScore:
    """Test cases for ReputationScore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.rep_score = ReputationScore(self.mock_client)

    def test_init_default_values(self):
        """Test ReputationScore initialization with default values."""
        rep = ReputationScore(self.mock_client)
        assert rep.recent_weight == 10
        assert rep.stale_weight == 5
        assert rep.pay_txn_multiplier == 1.0
        assert rep.asset_transfer_points == 10.0
        assert rep.app_call_points == 20.0
        assert rep.high_frequency_penalty_threshold == 1000
        assert rep.high_frequency_penalty == -10.0
        assert rep.normal_activity_reward == 10.0
        assert rep.inactivity_penalty == -10.0
        assert rep.asa_holding_multiplier == 0.1
        assert rep.normalization_cap == 100.0

    def test_init_custom_values(self):
        """Test ReputationScore initialization with custom values."""
        rep = ReputationScore(
            self.mock_client,
            recent_weight=15,
            stale_weight=8,
            pay_txn_multiplier=2.0,
            asset_transfer_points=15.0,
            app_call_points=25.0,
            asa_holding_multiplier=0.2,
        )
        assert rep.recent_weight == 15
        assert rep.stale_weight == 8
        assert rep.pay_txn_multiplier == 2.0
        assert rep.asset_transfer_points == 15.0
        assert rep.app_call_points == 25.0
        assert rep.asa_holding_multiplier == 0.2

    def test_calculate_recency_weight_recent(self):
        """Test recency weight calculation for recent transactions."""
        now = datetime.now().timestamp()
        recent_timestamp = now - (30 * 24 * 60 * 60)  # 30 days ago

        weight = self.rep_score.calculate_recency_weight(recent_timestamp)
        assert weight == self.rep_score.recent_weight

    def test_calculate_recency_weight_stale(self):
        """Test recency weight calculation for stale transactions."""
        now = datetime.now().timestamp()
        stale_timestamp = now - (200 * 24 * 60 * 60)  # 200 days ago (> 6 months)

        weight = self.rep_score.calculate_recency_weight(stale_timestamp)
        assert weight == self.rep_score.stale_weight

    def test_transaction_frequency_score_normal(self):
        """Test frequency score for normal activity."""
        transactions = [{"tx-type": "pay"}] * 50  # 50 transactions
        score = self.rep_score.transaction_frequency_score(transactions)
        assert score == self.rep_score.normal_activity_reward

    def test_transaction_frequency_score_high_frequency(self):
        """Test frequency score for high frequency (spam)."""
        transactions = [{"tx-type": "pay"}] * 1500  # 1500 transactions (> threshold)
        score = self.rep_score.transaction_frequency_score(transactions)
        assert score == self.rep_score.high_frequency_penalty

    def test_transaction_frequency_score_no_transactions(self):
        """Test frequency score with no transactions."""
        transactions = []
        score = self.rep_score.transaction_frequency_score(transactions)
        assert score == 0.0

    def test_apply_reputation_decay_active(self):
        """Test reputation decay for active account."""
        now = datetime.now().timestamp()
        recent_timestamp = now - (30 * 24 * 60 * 60)  # 30 days ago

        decay = self.rep_score.apply_reputation_decay(recent_timestamp)
        assert decay == 0.0

    def test_apply_reputation_decay_inactive(self):
        """Test reputation decay for inactive account."""
        now = datetime.now().timestamp()
        old_timestamp = now - (200 * 24 * 60 * 60)  # 200 days ago

        decay = self.rep_score.apply_reputation_decay(old_timestamp)
        assert decay == self.rep_score.inactivity_penalty

    def test_apply_reputation_decay_no_timestamp(self):
        """Test reputation decay with no timestamp."""
        decay = self.rep_score.apply_reputation_decay(0)
        assert decay == self.rep_score.inactivity_penalty

    def test_calculate_reputation_pay_transaction(self):
        """Test reputation calculation for payment transactions."""
        transactions = [
            {
                "tx-type": "pay",
        ]

        self.mock_client.fetch_transactions.return_value = transactions
        self.mock_client.fetch_asa_holdings.return_value = asa_holdings
        score = self.rep_score.get_reputation_score(VALID_ADDR)

        # Calculate expected raw score
        raw_score = (
            (1.0 * self.rep_score.recent_weight * self.rep_score.pay_txn_multiplier)
            + self.rep_score.normal_activity_reward
            + (0.5 * self.rep_score.asa_holding_multiplier)
            + (1.0 * self.rep_score.asa_holding_multiplier)
        )

        expected_normalized = min(
            (raw_score / self.rep_score.normalization_cap) * 100.0, 100.0
        )
        assert score == round(expected_normalized, 2)

    def test_get_reputation_score_no_asa_holdings(self):
        """Test reputation score calculation without ASA holdings."""
        transactions = [
            {
                "tx-type": "pay",
                "round-time": datetime.now().timestamp(),
                "payment-transaction": {"amount": 1000000},
            }
        ]

        self.mock_client.fetch_transactions.return_value = transactions
        self.mock_client.fetch_asa_holdings.return_value = []
        score = self.rep_score.get_reputation_score(VALID_ADDR)

        raw_score = (
            (1.0 * self.rep_score.recent_weight * self.rep_score.pay_txn_multiplier)
            + self.rep_score.normal_activity_reward
        )

        expected_normalized = (raw_score / self.rep_score.normalization_cap) * 100.0
        assert score == round(expected_normalized, 2)

    def test_transaction_with_missing_fields(self):
        """Test handling of transactions with missing fields."""
        transactions = [
            {
                "tx-type": "pay",
                "round-time": datetime.now().timestamp(),
            },  # Missing payment-transaction
            {"tx-type": "axfer", "round-time": datetime.now().timestamp()},
            {
                "tx-type": "unknown",
                "round-time": datetime.now().timestamp(),
            },  # Unknown type
        ]

        self.mock_client.fetch_transactions.return_value = transactions
        score = self.rep_score.calculate_reputation(VALID_ADDR)
        # Should only count axfer transaction
        expected_score = (
            self.rep_score.asset_transfer_points * self.rep_score.recent_weight
        ) + self.rep_score.normal_activity_reward
        assert score == expected_score

    def test_six_months_constant(self):
        """Test the SIX_MONTHS_SECONDS constant is reasonable."""
        # Approximately 6 months in seconds
        expected_seconds = 60 * 60 * 24 * 30 * 6
        assert ReputationScore.SIX_MONTHS_SECONDS == expected_seconds
