"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import Mock
from algorand_reputation.client import AlgorandClient
from algorand_reputation.reputation import ReputationScore


@pytest.fixture
def mock_client():
    """Create a mock AlgorandClient for testing."""
    return Mock(spec=AlgorandClient)


@pytest.fixture
def reputation_score(mock_client):
    """Create a ReputationScore instance with mock client."""
    return ReputationScore(mock_client)


@pytest.fixture
def sample_transactions():
    """Create sample transaction data for testing."""
    import time
    current_time = time.time()

    return [
        {
            "tx-type": "pay",
            "round-time": current_time - (24 * 60 * 60),  # 1 day ago
            "payment-transaction": {"amount": 1000000}  # 1 ALGO
        },
        {
            "tx-type": "axfer",
            "round-time": current_time - (2 * 24 * 60 * 60),  # 2 days ago
        },
        {
            "tx-type": "appl",
            "round-time": current_time - (3 * 24 * 60 * 60),  # 3 days ago
        }
    ]


@pytest.fixture
def sample_asa_holdings():
    """Create sample ASA holdings data for testing."""
    return [
        {"asset-id": 1, "amount": 500000},  # 0.5 units
        {"asset-id": 2, "amount": 1000000},  # 1.0 unit
        {"asset-id": 3, "amount": 2500000},  # 2.5 units
    ]


@pytest.fixture
def old_transactions():
    """Create old transaction data for testing inactivity."""
    import time
    old_time = time.time() - (200 * 24 * 60 * 60)  # 200 days ago

    return [
        {
            "tx-type": "pay",
            "round-time": old_time,
            "payment-transaction": {"amount": 500000}  # 0.5 ALGO
        }
    ]


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("ALGOD_API_KEY", "test_api_key")
        yield m


@pytest.fixture
def real_client():
    """Create a real AlgorandClient for integration tests."""
    # Only use in integration tests that actually call the API
    return AlgorandClient(network_choice="testnet", purestake_token="test_key")
