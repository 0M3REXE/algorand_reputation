from datetime import datetime

class ReputationScore:
    def __init__(self, client):
        self.client = client

    def calculate_recency_weight(self, timestamp):
        current_time = datetime.now().timestamp()
        time_diff = current_time - timestamp
        return 10 if time_diff < 15768000 else 5

    def transaction_frequency_score(self, account_address):
        transactions = self.client.fetch_transactions(account_address)
        frequency = len(transactions) / 365  # Normalize by days (for 1 year)
        if frequency > 1000:
            return -10  # Penalize very high frequency
        else:
            return 10  # Reward regular activity

    def apply_reputation_decay(self, last_transaction_time):
        current_time = datetime.now().timestamp()
        inactivity_period = current_time - last_transaction_time
        if inactivity_period > 15768000:  # More than 6 months
            return -10  # Subtract points for inactivity
        return 0

    def calculate_reputation(self, account_address):
        transactions = self.client.fetch_transactions(account_address)
        if not transactions:
            return 0

        score = 0
        last_transaction_time = 0

        for txn in transactions:
            recency_weight = self.calculate_recency_weight(txn['round-time'])
            
            if txn['tx-type'] == 'pay':  # Payment transaction
                amount_sent = txn['payment-transaction']['amount'] / 1e6
                score += amount_sent * recency_weight
            elif txn['tx-type'] == 'axfer':  # Asset transfer transaction
                score += 10 * recency_weight
            elif txn['tx-type'] == 'appl':  # Smart contract interaction
                score += 20  # Participation in smart contracts

            last_transaction_time = max(last_transaction_time, txn['round-time'])

        score += self.transaction_frequency_score(account_address)
        score += self.apply_reputation_decay(last_transaction_time)

        return score

    def normalize_score(self, raw_score):
        max_possible_score = 100  # Estimated maximum score based on different factors
        normalized_score = min((raw_score / max_possible_score) * 100, 100)
        return round(normalized_score, 1)

    def get_reputation_score(self, account_address):
        raw_score = self.calculate_reputation(account_address)
        
        assets = self.client.fetch_asa_holdings(account_address)
        if assets:
            for asset in assets:
                raw_score += asset['amount'] / 1e6 * 0.1  # Small boost based on ASA holdings

        return self.normalize_score(raw_score)
