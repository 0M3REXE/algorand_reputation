"""Unit tests for ReputationScore."""

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

    """Unit tests for ReputationScore."""

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
            now = datetime.now().timestamp()
            recent_timestamp = now - (30 * 24 * 60 * 60)
            weight = self.rep_score.calculate_recency_weight(recent_timestamp)
            assert weight == self.rep_score.recent_weight

        def test_calculate_recency_weight_stale(self):
            now = datetime.now().timestamp()
            stale_timestamp = now - (200 * 24 * 60 * 60)
            weight = self.rep_score.calculate_recency_weight(stale_timestamp)
            assert weight == self.rep_score.stale_weight

        def test_transaction_frequency_score_normal(self):
            transactions = [{"tx-type": "pay"}] * 50
            score = self.rep_score.transaction_frequency_score(transactions)
            assert score == self.rep_score.normal_activity_reward

        def test_transaction_frequency_score_high_frequency(self):
            transactions = [{"tx-type": "pay"}] * 1500
            score = self.rep_score.transaction_frequency_score(transactions)
            assert score == self.rep_score.high_frequency_penalty

        def test_transaction_frequency_score_no_transactions(self):
            transactions = []
            score = self.rep_score.transaction_frequency_score(transactions)
            assert score == 0.0

        def test_apply_reputation_decay_active(self):
            now = datetime.now().timestamp()
            recent_timestamp = now - (30 * 24 * 60 * 60)
            decay = self.rep_score.apply_reputation_decay(recent_timestamp)
            assert decay == 0.0

        def test_apply_reputation_decay_inactive(self):
            now = datetime.now().timestamp()
            old_timestamp = now - (200 * 24 * 60 * 60)
            decay = self.rep_score.apply_reputation_decay(old_timestamp)
            assert decay == self.rep_score.inactivity_penalty

        def test_apply_reputation_decay_no_timestamp(self):
            decay = self.rep_score.apply_reputation_decay(0)
            assert decay == self.rep_score.inactivity_penalty

        def test_calculate_reputation_pay_transaction(self):
            transactions = [
                {
                    "tx-type": "pay",
                    "round-time": datetime.now().timestamp(),
                    "payment-transaction": {"amount": 1000000},
                }
            ]
            self.mock_client.fetch_transactions.return_value = transactions
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            expected_score = (
                1.0 * self.rep_score.recent_weight * self.rep_score.pay_txn_multiplier
            ) + self.rep_score.normal_activity_reward
            assert score == expected_score

        def test_calculate_reputation_asset_transfer(self):
            transactions = [
                {"tx-type": "axfer", "round-time": datetime.now().timestamp()}
            ]
            self.mock_client.fetch_transactions.return_value = transactions
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            expected_score = (
                self.rep_score.asset_transfer_points * self.rep_score.recent_weight
            ) + self.rep_score.normal_activity_reward
            assert score == expected_score

        def test_calculate_reputation_app_call(self):
            transactions = [
                {"tx-type": "appl", "round-time": datetime.now().timestamp()}
            ]
            self.mock_client.fetch_transactions.return_value = transactions
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            expected_score = (
                self.rep_score.app_call_points + self.rep_score.normal_activity_reward
            )
            assert score == expected_score

        def test_calculate_reputation_mixed_transactions(self):
            now = datetime.now().timestamp()
            transactions = [
                {"tx-type": "pay", "round-time": now, "payment-transaction": {"amount": 1000000}},
                {"tx-type": "axfer", "round-time": now},
                {"tx-type": "appl", "round-time": now},
            ]
            self.mock_client.fetch_transactions.return_value = transactions
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            expected_score = (
                (1.0 * self.rep_score.recent_weight * self.rep_score.pay_txn_multiplier)
                + (self.rep_score.asset_transfer_points * self.rep_score.recent_weight)
                + self.rep_score.app_call_points
                + self.rep_score.normal_activity_reward
            )
            assert score == expected_score

        def test_calculate_reputation_no_transactions(self):
            self.mock_client.fetch_transactions.return_value = []
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            assert score == 0.0

        def test_normalize_score_normal_range(self):
            raw_score = 50.0
            normalized = self.rep_score.normalize_score(raw_score)
            expected = (raw_score / self.rep_score.normalization_cap) * 100.0
            assert normalized == expected

        def test_normalize_score_above_cap(self):
            raw_score = 150.0
            normalized = self.rep_score.normalize_score(raw_score)
            assert normalized == 100.0

        def test_normalize_score_zero_cap(self):
            rep = ReputationScore(self.mock_client, normalization_cap=0.0)
            normalized = rep.normalize_score(50.0)
            assert normalized == 0.0

        def test_get_reputation_score_with_asa_holdings(self):
            transactions = [
                {
                    "tx-type": "pay",
                    "round-time": datetime.now().timestamp(),
                    "payment-transaction": {"amount": 1000000},
                }
            ]
            asa_holdings = [{"amount": 500000}, {"amount": 1000000}]
            self.mock_client.fetch_transactions.return_value = transactions
            self.mock_client.fetch_asa_holdings.return_value = asa_holdings
            score = self.rep_score.get_reputation_score(VALID_ADDR)
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
            transactions = [
                {"tx-type": "pay", "round-time": datetime.now().timestamp()},
                {"tx-type": "axfer", "round-time": datetime.now().timestamp()},
                {"tx-type": "unknown", "round-time": datetime.now().timestamp()},
            ]
            self.mock_client.fetch_transactions.return_value = transactions
            score = self.rep_score.calculate_reputation(VALID_ADDR)
            expected_score = (
                self.rep_score.asset_transfer_points * self.rep_score.recent_weight
            ) + self.rep_score.normal_activity_reward
            assert score == expected_score

        def test_six_months_constant(self):
            expected_seconds = 60 * 60 * 24 * 30 * 6
            assert ReputationScore.SIX_MONTHS_SECONDS == expected_seconds
