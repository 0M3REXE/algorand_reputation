# Algorand Reputation Score

**Algorand Reputation Score** is a Python package designed to evaluate the reputation of Algorand accounts based on their transaction history, asset holdings, and activity patterns. This tool can help determine the credibility of an Algorand address by analyzing its behavior on the blockchain.

## Features

- **Recency Weighting:** Scores transactions based on how recent they are.
- **Transaction Frequency Score:** Evaluates account activity frequency and applies penalties or rewards accordingly.
- **Reputation Decay:** Reduces the score for accounts that show inactivity over time.
- **Asset Holdings:** Considers the amount of ASA (Algorand Standard Assets) held by an account.
- **Testnet/Mainnet:** It works on both testnet and main net

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/0M3REXE/algorand_reputation
   cd algorand_reputation
   pip install .
   
