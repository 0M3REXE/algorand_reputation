#!/usr/bin/env python3
"""
Enhanced Algorand Reputation Score Examples

This script demonstrates the new features of the enhanced ReputationScore class,
including detailed analysis, batch processing, and comparative insights.
"""

import os
from algorand_reputation import AlgorandClient, ReputationScore


def main():
    """Demonstrate enhanced reputation scoring features."""

    # Initialize client (replace with your API key)
    api_key = os.getenv("ALGOD_API_KEY", "your_api_key_here")
    client = AlgorandClient(network_choice="testnet", purestake_token=api_key)
    rep = ReputationScore(client)

    # Example addresses (replace with real addresses for testing)
    test_addresses = [
        "GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A",
        "EW64GC6F24M7NDSC5R3ES4YUVEHDWOXRGTJX3ENGB3OFPQKYGVB5TGBBZM",
        # Add more addresses as needed
    ]

    print("=== Enhanced Algorand Reputation Analysis ===\n")

    # 1. Get detailed reputation for a single address
    if test_addresses:
        print("1. Detailed Reputation Analysis:")
        print("-" * 40)

        detailed_rep = rep.get_detailed_reputation(test_addresses[0])
        print(f"Address: {test_addresses[0]}")
        print(f"Reputation Score: {detailed_rep['reputation_score']}")
        print(f"Raw Score: {detailed_rep['raw_score']:.2f}")

        print("\nScore Breakdown:")
        for component, score in detailed_rep['breakdown'].items():
            print(f"  {component}: {score:.2f}")

        print("\nAnalysis:")
        analysis = detailed_rep['analysis']
        print(f"  Total Transactions: {analysis['total_transactions']}")
        print(f"  Unique Receivers: {analysis['unique_receivers']}")
        print(f"  Total Volume: {analysis['total_volume']:.2f} ALGO")
        print(f"  ASA Holdings: {analysis['asa_holdings_count']}")

        if analysis['transaction_types']:
            print(f"  Transaction Types: {analysis['transaction_types']}")

    # 2. Batch processing multiple addresses
    print("\n\n2. Batch Reputation Analysis:")
    print("-" * 40)

    if len(test_addresses) > 1:
        batch_results = rep.get_batch_reputation_scores(test_addresses)

        for addr, result in batch_results.items():
            if "error" in result:
                print(f"{addr}: Error - {result['error']}")
            else:
                print(f"{addr}: {result['reputation_score']} "
                      f"({result['analysis']['total_transactions']} txns)")
    else:
        print("Add more addresses to test_addresses list for batch analysis")

    # 3. Comparative analysis
    print("\n\n3. Comparative Analysis:")
    print("-" * 40)

    if len(test_addresses) > 1:
        comparison = rep.compare_accounts(test_addresses)

        print("Ranking:")
        for item in comparison['ranking']:
            print(f"  #{item['rank']}: {item['address'][:10]}... "
                  f"Score: {item['score']}")

        summary = comparison['summary']
        print("\nSummary:")
        print(f"  Total Accounts: {summary['total_accounts']}")
        print(f"  Valid Accounts: {summary['valid_accounts']}")
        print(f"  Average Score: {summary['average_score']:.2f}")
        print(f"  Highest Score: {summary['highest_score']:.2f}")
        print(f"  Lowest Score: {summary['lowest_score']:.2f}")
    else:
        print("Add more addresses to test_addresses list for comparison")

    # 4. Export data
    print("\n\n4. Data Export:")
    print("-" * 40)

    try:
        # Export as JSON
        json_data = rep.export_reputation_data(test_addresses, format="json")
        print("JSON Export (first 200 chars):")
        print(json_data[:200] + "...")

        # Export as CSV
        csv_data = rep.export_reputation_data(test_addresses, format="csv")
        print("\nCSV Export:")
        print(csv_data)

    except Exception as e:
        print(f"Export failed: {e}")

    # 5. Reputation insights
    print("\n\n5. Reputation Insights:")
    print("-" * 40)

    try:
        insights = rep.get_reputation_insights(test_addresses)
        print(f"Total Accounts Analyzed: {insights['total_accounts_analyzed']}")
        print(f"High Score Accounts (≥70): {insights['high_score_accounts']}")
        print(f"High Score Percentage: {insights['high_score_percentage']:.1f}%")

        if insights['transaction_type_distribution']:
            print(f"Most Common Transaction Type: {insights['most_common_txn_type']}")
            print("Transaction Type Distribution:")
            for tx_type, count in insights['transaction_type_distribution'].items():
                print(f"  {tx_type}: {count}")

        score_dist = insights['score_distribution']
        print("\nScore Distribution:")
        print(f"  Excellent (≥90): {score_dist['excellent']}")
        print(f"  Good (70-89): {score_dist['good']}")
        print(f"  Fair (50-69): {score_dist['fair']}")
        print(f"  Poor (<50): {score_dist['poor']}")

    except Exception as e:
        print(f"Insights analysis failed: {e}")

    print("\n=== Analysis Complete ===")


if __name__ == "__main__":
    main()
