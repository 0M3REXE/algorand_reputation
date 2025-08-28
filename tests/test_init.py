"""Unit tests for package initialization."""

from algorand_reputation import AlgorandClient, ReputationScore


class TestPackageImports:
    """Test cases for package imports and initialization."""

    def test_algorand_client_import(self):
        """Test that AlgorandClient can be imported from package."""
        assert AlgorandClient is not None
        # Verify it's the correct class
        assert hasattr(AlgorandClient, '__init__')
        assert hasattr(AlgorandClient, 'fetch_account_balance')
        assert hasattr(AlgorandClient, 'fetch_transactions')
        assert hasattr(AlgorandClient, 'fetch_asa_holdings')

    def test_reputation_score_import(self):
        """Test that ReputationScore can be imported from package."""
        assert ReputationScore is not None
        # Verify it's the correct class
        assert hasattr(ReputationScore, '__init__')
        assert hasattr(ReputationScore, 'calculate_reputation')
        assert hasattr(ReputationScore, 'get_reputation_score')
        assert hasattr(ReputationScore, 'normalize_score')

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        from algorand_reputation import __all__
        expected_exports = ["AlgorandClient", "ReputationScore"]
        assert __all__ == expected_exports

    def test_classes_are_different(self):
        """Test that imported classes are different classes."""
        assert AlgorandClient != ReputationScore
        assert isinstance(AlgorandClient, type)
        assert isinstance(ReputationScore, type)
