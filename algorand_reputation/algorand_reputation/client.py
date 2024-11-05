from algosdk.v2client import algod, indexer
from datetime import datetime

class AlgorandClient:
    def __init__(self, network_choice, purestake_token):
        if network_choice == "mainnet":
            self.algod_address = "https://mainnet-api.4160.nodely.dev"
            self.indexer_address = "https://mainnet-idx.4160.nodely.dev"
        else:
            self.algod_address = "https://testnet-api.4160.nodely.dev"
            self.indexer_address = "https://testnet-idx.4160.nodely.dev"

        self.headers = {"X-API-Key": purestake_token}
        self.algod_client = algod.AlgodClient(purestake_token, self.algod_address, self.headers)
        self.indexer_client = indexer.IndexerClient(purestake_token, self.indexer_address, self.headers)

    def fetch_account_balance(self, account_address):
        try:
            account_info = self.algod_client.account_info(account_address)
            algo_balance = account_info['amount'] / 1e6  # Balance in Algos
            return algo_balance
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return None

    def fetch_transactions(self, account_address):
        try:
            response = self.indexer_client.search_transactions_by_address(account_address)
            transactions = response['transactions']
            return transactions
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return None

    def fetch_asa_holdings(self, account_address):
        try:
            response = self.indexer_client.lookup_account_assets(account_address)
            assets = response['assets']
            return assets
        except Exception as e:
            print(f"Error fetching ASA holdings: {e}")
            return None
