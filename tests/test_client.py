"""Unit tests for AlgorandClient."""

import os
import pytest
from unittest.mock import patch
from algorand_reputation.client import AlgorandClient, NETWORKS


class TestAlgorandClient:
    """Test cases for AlgorandClient class."""

    def test_init_with_valid_network(self):
        """Test client initialization with valid network."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")
            assert client.network_choice == "testnet"
            assert client.algod_address == NETWORKS["testnet"]["algod"]
            assert client.indexer_address == NETWORKS["testnet"]["indexer"]

    def test_init_with_invalid_network_defaults_to_testnet(self):
        """Test client initialization with invalid network defaults to testnet."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="invalid")
            assert client.network_choice == "testnet"

    def test_init_with_mainnet(self):
        """Test client initialization with mainnet."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="mainnet")
            assert client.network_choice == "mainnet"
            assert client.algod_address == NETWORKS["mainnet"]["algod"]
            assert client.indexer_address == NETWORKS["mainnet"]["indexer"]

    def test_init_with_token_parameter(self):
        """Test client initialization with token parameter."""
        client = AlgorandClient(network_choice="testnet", purestake_token="custom_key")
        assert client.headers["X-API-Key"] == "custom_key"

    def test_init_without_token_raises_error(self):
        """Test client initialization without token raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing PureStake"):
                AlgorandClient(network_choice="testnet")

    def test_init_with_rate_limit(self):
        """Test client initialization with rate limiting."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet", rate_limit_per_sec=10.0)
            assert client._rate_limit_per_sec == 10.0
            assert client._min_interval == 0.1

    def test_throttle_no_rate_limit(self):
        """Test throttle method with no rate limiting."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")
            # Should not raise any errors
            client._throttle()

    @patch('time.sleep')
    @patch('time.time')
    def test_throttle_with_rate_limit(self, mock_time, mock_sleep):
        """Test throttle method with rate limiting."""
        mock_time.side_effect = [0.0, 0.05]  # First call at 0, second at 0.05

        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet", rate_limit_per_sec=10.0)
            client._last_call_time = 0.0
            client._throttle()

            # Should sleep for 0.05 seconds to maintain 0.1s interval
            mock_sleep.assert_called_once_with(0.05)

    def test_fetch_account_balance_success(self):
        """Test successful account balance fetch."""
        mock_response = {"amount": 1000000}  # 1 ALGO in microalgos

        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.algod_client, 'account_info', return_value=mock_response):
                result = client.fetch_account_balance("test_address")
                assert result == 1.0

    def test_fetch_account_balance_error(self):
        """Test account balance fetch with error."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.algod_client, 'account_info', side_effect=Exception("Network error")):
                result = client.fetch_account_balance("test_address")
                assert result is None

    def test_fetch_transactions_success(self):
        """Test successful transaction fetch."""
        mock_response = {"transactions": [{"tx-type": "pay"}, {"tx-type": "axfer"}]}

        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.indexer_client, 'search_transactions_by_address', return_value=mock_response):
                result = client.fetch_transactions("test_address", limit=100)
                assert len(result) == 2
                assert result[0]["tx-type"] == "pay"

    def test_fetch_transactions_error(self):
        """Test transaction fetch with error."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.indexer_client, 'search_transactions_by_address', side_effect=Exception("Network error")):
                result = client.fetch_transactions("test_address")
                assert result == []

    def test_fetch_asa_holdings_success(self):
        """Test successful ASA holdings fetch."""
        mock_response = {"assets": [{"asset-id": 1, "amount": 100}, {"asset-id": 2, "amount": 200}]}

        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.indexer_client, 'lookup_account_assets', return_value=mock_response):
                result = client.fetch_asa_holdings("test_address")
                assert len(result) == 2
                assert result[0]["asset-id"] == 1

    def test_fetch_asa_holdings_error(self):
        """Test ASA holdings fetch with error."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="testnet")

            with patch.object(client.indexer_client, 'lookup_account_assets', side_effect=Exception("Network error")):
                result = client.fetch_asa_holdings("test_address")
                assert result == []

    def test_network_method(self):
        """Test network method returns correct network choice."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="mainnet")
            assert client.network() == "mainnet"

    def test_case_insensitive_network_choice(self):
        """Test network choice is case insensitive."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="MAINNET")
            assert client.network_choice == "mainnet"

    def test_whitespace_stripping_network_choice(self):
        """Test network choice has whitespace stripped."""
        with patch.dict(os.environ, {"ALGOD_API_KEY": "test_key"}):
            client = AlgorandClient(network_choice="  testnet  ")
            assert client.network_choice == "testnet"
