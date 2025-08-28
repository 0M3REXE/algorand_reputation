# Algorand Reputation Score

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Advanced heuristic reputation scoring utilities for Algorand accounts. Analyzes comprehensive on-chain activity including payments, ASA transfers, app calls, asset configurations, freezes, and key registrations to produce a sophisticated 0–100 reputation score.

> **Disclaimer**: Experimental heuristic. Do not rely on it alone for financial, compliance, or security decisions.

## ✨ Enhanced Features

| Aspect | What it does |
| ------ | ------------ |
| **Multi-Transaction Support** | Handles payments, asset transfers, app calls, asset configs, freezes, and key registrations |
| **Advanced Pattern Analysis** | Analyzes transaction patterns, receiver diversity, and volume metrics |
| **Smart Scoring** | Large transaction bonuses, frequency analysis, and inactivity decay |
| **Detailed Analytics** | Comprehensive score breakdowns and transaction insights |
| **Batch Processing** | Efficient analysis of multiple accounts simultaneously |
| **Export Capabilities** | JSON and CSV export for data analysis and reporting |
| **Comparative Analysis** | Account ranking and comparative insights across multiple addresses |
| **Highly Configurable** | 15+ adjustable parameters for fine-tuned scoring |

## 🚀 Installation

### Basic Installation
```bash
git clone https://github.com/0M3REXE/algorand_reputation
cd algorand_reputation
pip install .
```

### Development Installation
```bash
pip install -e .[dev]
```

## 🔑 API Key Setup

You need an Algod/Indexer API key from [PureStake](https://purestake.com/) or [Nodely](https://nodely.io).

### Option 1: Environment Variable
```powershell
$env:ALGOD_API_KEY = "YOUR_API_KEY"
```

### Option 2: Direct Parameter
```python
client = AlgorandClient(network_choice="testnet", purestake_token="YOUR_API_KEY")
```

## 📖 Quick Start

```python
from algorand_reputation import AlgorandClient, ReputationScore

# Initialize client
client = AlgorandClient(network_choice="testnet", purestake_token="YOUR_API_KEY")

# Basic reputation scoring
rep = ReputationScore(client)
score = rep.get_reputation_score("ACCOUNT_ADDRESS")
print(f"Reputation Score: {score}")
```

## 🎯 Advanced Usage

### Detailed Reputation Analysis

```python
# Get comprehensive reputation breakdown
detailed = rep.get_detailed_reputation("ACCOUNT_ADDRESS")

print(f"Overall Score: {detailed['reputation_score']}")
print(f"Raw Score: {detailed['raw_score']}")

# Score breakdown
breakdown = detailed['breakdown']
print(f"Transaction Score: {breakdown['transaction_score']}")
print(f"Frequency Score: {breakdown['frequency_score']}")
print(f"Pattern Bonuses: {breakdown['pattern_bonuses']}")

# Transaction analysis
analysis = detailed['analysis']
print(f"Total Transactions: {analysis['total_transactions']}")
print(f"Unique Receivers: {analysis['unique_receivers']}")
print(f"Transaction Types: {analysis['transaction_types']}")
```

### Batch Processing

```python
# Analyze multiple accounts efficiently
addresses = [
    "ADDRESS_1",
    "ADDRESS_2",
    "ADDRESS_3"
]

batch_results = rep.get_batch_reputation_scores(addresses)
for addr, result in batch_results.items():
    print(f"{addr}: {result['reputation_score']}")
```

### Comparative Analysis

```python
# Compare and rank multiple accounts
comparison = rep.compare_accounts(addresses)

print("🏆 Ranking:")
for rank in comparison['ranking']:
    print(f"#{rank['rank']}: {rank['address'][:10]}... Score: {rank['score']}")

print(f"\n📊 Summary:")
print(f"Average Score: {comparison['summary']['average_score']:.2f}")
print(f"Highest Score: {comparison['summary']['highest_score']:.2f}")
```

### Data Export

```python
# Export as JSON
json_data = rep.export_reputation_data(addresses, format="json")

# Export as CSV
csv_data = rep.export_reputation_data(addresses, format="csv")
print(csv_data)
```

### Advanced Configuration

```python
rep = ReputationScore(
    client,
    # Transaction type weights
    recent_weight=12,
    stale_weight=4,
    pay_txn_multiplier=1.2,
    asset_transfer_points=15.0,
    app_call_points=25.0,
    asset_config_points=18.0,
    asset_freeze_points=8.0,
    keyreg_points=30.0,

    # Advanced features
    large_transaction_bonus=1.5,
    large_transaction_threshold=10.0,
    receiver_diversity_bonus=8.0,
    min_unique_receivers=3,

    # Scoring parameters
    high_frequency_penalty_threshold=1500,
    high_frequency_penalty=-15.0,
    normal_activity_reward=12.0,
    inactivity_penalty=-12.0,
    asa_holding_multiplier=0.08,
    normalization_cap=120.0,
)
```

## 📊 Scoring Algorithm

### Enhanced Scoring Process

1. **Transaction Analysis**: Score each transaction by type × recency weight
2. **Pattern Recognition**: Analyze transaction patterns and receiver diversity
3. **Volume Assessment**: Apply bonuses for large transactions
4. **Frequency Evaluation**: Add rewards for normal usage, penalties for spam
5. **Activity Decay**: Apply penalties for prolonged inactivity (>6 months)
6. **Asset Holdings**: Add bonuses for ASA holdings
7. **Normalization**: Scale final score to 0–100 range

### Transaction Types Supported

- **Payment (pay)**: ALGO transfers with volume-based bonuses
- **Asset Transfer (axfer)**: ASA transfers
- **Application Call (appl)**: Smart contract interactions
- **Asset Configuration (acfg)**: ASA creation/modification
- **Asset Freeze (afrz)**: ASA freeze operations
- **Key Registration (keyreg)**: Participation key registration

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=algorand_reputation --cov-report=html

# Run specific test file
pytest tests/test_reputation.py -v
```

## 📈 Examples

Check out the `examples/` directory for comprehensive usage examples:

- `enhanced_reputation_demo.py` - Complete demonstration of all features
- Additional examples for specific use cases

## 🔧 Development

### Project Structure
```
algorand_reputation/
├── algorand_reputation/
│   ├── __init__.py          # Package initialization
│   ├── client.py            # Algorand API client
│   └── reputation.py        # Reputation scoring logic
├── examples/
│   └── enhanced_reputation_demo.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_client.py       # Client tests
│   ├── test_reputation.py   # Reputation tests
│   └── test_init.py         # Package tests
├── pytest.ini              # Test configuration
├── pyproject.toml          # Build configuration
├── setup.py               # Package setup
└── README.md
```

### Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type checking
mypy algorand_reputation/
```

## 🛣️ Roadmap

- [ ] **Pagination Support**: Deeper transaction history analysis
- [ ] **Governance Integration**: Staking and governance participation signals
- [ ] **CLI Tool**: Command-line interface for reputation checking
- [ ] **Web Dashboard**: Browser-based reputation analysis interface
- [ ] **Database Integration**: Historical reputation data storage
- [ ] **Real-time Monitoring**: Continuous reputation tracking
- [ ] **Machine Learning**: AI-powered reputation prediction
- [ ] **Multi-network Support**: Support for additional Algorand networks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Add tests for new features
- Update documentation
- Follow PEP 8 style guidelines
- Keep logic transparent and explainable

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Reliability Notes

- Network failures return empty data; scores may default to low
- API rate limits may affect analysis speed
- Results are heuristic-based and should be combined with additional analytics
- Regular updates recommended for evolving scoring algorithms

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/0M3REXE/algorand_reputation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/0M3REXE/algorand_reputation/discussions)

---

**Made with ❤️ for the Algorand ecosystem**

