from algorand_reputation.client import AlgorandClient
from algorand_reputation.reputation import ReputationScore # Initialize the client
client = AlgorandClient(network_choice="testnet",purestake_token="")
reputation = ReputationScore(client)  # Get account address and calculate reputation score 
account_address = "Account Address" 
reputation_score = reputation.get_reputation_score(account_address) 
print(f"Reputation score for account {account_address}: {reputation_score}/100")