# Algorand Reputation Score

Heuristic reputation scoring utilities for Algorand accounts. It analyzes on‑chain activity (payments, ASA transfers, app calls), recency, frequency, inactivity, and ASA holdings to produce a 0–100 score.

> Disclaimer: Experimental heuristic. Do not rely on it alone for financial, compliance, or security decisions.

## Features
| Aspect | What it does |
| ------ | ------------ |
| Recency | Recent transactions weigh more than older ones |
| Types | Distinguishes payments, asset transfers, app calls |
| Frequency | Rewards normal usage; penalizes extreme spam |
| Inactivity | Decay if no transactions ~6+ months |
| ASA Holdings | Optional small boost for holdings |
| Configurable | All weights adjustable in constructor |

## Installation
Clone and install (flattened package structure):
```powershell
git clone https://github.com/0M3REXE/algorand_reputation
cd algorand_reputation/algorand_reputation
pip install .
```

Dev / tests:
```powershell
pip install -e .[dev]
```

## API Key Setup
You need an algod/indexer API key (PureStake / Nodely). Set it (PowerShell):
```powershell
$env:ALGOD_API_KEY = "YOUR_KEY"
```
Or pass `purestake_token` directly when creating the client.

## Quick Start
```python
from algorand_reputation import AlgorandClient, ReputationScore

client = AlgorandClient(network_choice="testnet", purestake_token="YOUR_KEY")  # omit purestake_token if env var set
rep = ReputationScore(client)
score = rep.get_reputation_score("ACCOUNT_ADDRESS")
print(f"Reputation: {score}")
```

## Customize Weights
```python
rep = ReputationScore(
   client,
   recent_weight=12,
   stale_weight=4,
   app_call_points=25,
   asa_holding_multiplier=0.05,
   normalization_cap=150,
)
```

## Access Raw Data
```python
balance = client.fetch_account_balance("ACCOUNT_ADDRESS")
txns = client.fetch_transactions("ACCOUNT_ADDRESS", limit=250)
assets = client.fetch_asa_holdings("ACCOUNT_ADDRESS")
```

## Scoring Steps
1. Score each transaction by type * recency weight
2. Add frequency reward / spam penalty
3. Apply inactivity decay (> ~6 months)
4. Add ASA holding multiplier
5. Normalize to 0–100 via `normalization_cap`

## Run Tests
```powershell
pytest -q
```

## Roadmap
* Pagination / deeper history
* Governance & staking signals
* CLI (`algorep score <addr>`) JSON output
* Weight auto-tuning

## Contributing
1. Open an issue
2. Add/adjust tests
3. Keep logic transparent & explainable

## License
MIT

## Reliability Notes
Network failures return empty lists; score may default low. Combine with additional analytics for critical use cases.

