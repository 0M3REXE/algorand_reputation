import time

from algorand_reputation.reputation import ReputationScore


class FakeClient:
    def __init__(self):
        now = int(time.time())
        # Two recent txns, one older than 6 months (simulate by subtracting seconds)
        self._txns = [
            {
                "round-time": now - 1000,
                "tx-type": "pay",
                "payment-transaction": {"amount": 5_000_000},
            },
            {"round-time": now - 2000, "tx-type": "axfer"},
            {"round-time": now - (60*60*24*30*7), "tx-type": "appl"},  # ~7 months old
        ]
        self._assets = [
            {"amount": 10_000_000},  # 10 units of an ASA (assuming decimals=6)
        ]

    def fetch_transactions(self, account_address, limit=1000):
        return list(self._txns)

    def fetch_asa_holdings(self, account_address):
        return list(self._assets)

    def fetch_account_balance(self, account_address):
        return 123.456


def test_reputation_score_basic():
    rep = ReputationScore(FakeClient())
    score = rep.get_reputation_score("TESTADDR")
    assert 0 <= score <= 100
    # Ensure ASA holding adds something (rough expectation)
    assert isinstance(score, float)
