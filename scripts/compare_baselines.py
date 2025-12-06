#!/usr/bin/env python3
"""
Baseline Comparison Script

Compares the agentic system against simple naive baselines:
- Rating-only ranking (sort by rating descending)
- Price-only ranking (sort by price ascending)

Usage:
    python compare_baselines.py --output-dir eval_results
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.buying_guide.app.session import run_agentic_session
from src.buying_guide.index import load_index


def load_test_queries(test_file: str) -> List[Dict]:
    """Load test queries from JSON file."""
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_queries']


def rating_only_baseline(query_text: str, top_k: int = 5) -> List[str]:
    """
    Baseline: Sort products by rating only (descending).
    
    Returns:
        List of top-k ASINs sorted by rating
    """
    products = load_index()
    
    # Sort by average rating (descending)
    sorted_products = sorted(
        products,
        key=lambda p: p.avg_rating_from_reviews or p.meta_average_rating or 0.0,
        reverse=True
    )
    
    return [p.asin for p in sorted_products[:top_k]]


def price_only_baseline(query_text: str, top_k: int = 5) -> List[str]:
    """
    Baseline: Sort products by price only (ascending - cheapest first).
    
    Returns:
        List of top-k ASINs sorted by price
    """
    products = load_index()
    
    # Filter out products without price and sort by price (ascending)
    products_with_price = [p for p in products if p.price is not None]
    sorted_products = sorted(products_with_price, key=lambda p: p.price)
    
    return [p.asin for p in sorted_products[:top_k]]


def calculate_relevance_match_rate(retrieved: List[str], relevant: List[str]) -> float:
    """Calculate what fraction of retrieved are relevant."""
    if not retrieved:
        return 0.0
    
    retrieved_set = set(retrieved)
    relevant_set = set(relevant)
    
    matched = retrieved_set.intersection(relevant_set)
    return len(matched) / len(retrieved)


def compare_systems(test_queries: List[Dict], k: int = 5) -> Dict:
    """
    Compare agentic system against baselines.
    
    Returns:
        Dictionary with comparison results
    """
    results = {
        'k': k,
        'queries': [],
        'aggregate': {
            'agentic_avg_relevance': 0.0,
            'rating_baseline_avg_relevance': 0.0,
            'price_baseline_avg_relevance': 0.0
        }
    }
    
    total_agentic_relevance = 0.0
    total_rating_relevance = 0.0
    total_price_relevance = 0.0
    
    for query_data in test_queries:
        query_id = query_data['query_id']
        query_text = query_data['query_text']
        relevant_asins = query_data['relevant_asins']
        
        print(f"\nQuery {query_id}: {query_text}")
        
        # Run agentic system
        try:
            agentic_result = run_agentic_session(query_text, top_k=k)
            agentic_asins = [p['asin'] for p in agentic_result.get('products', [])][:k]
        except Exception as e:
            print(f"  Agentic Error: {e}")
            agentic_asins = []
        
        # Run baselines
        rating_asins = rating_only_baseline(query_text, top_k=k)
        price_asins = price_only_baseline(query_text, top_k=k)
        
        # Calculate relevance
        agentic_rel = calculate_relevance_match_rate(agentic_asins, relevant_asins)
        rating_rel = calculate_relevance_match_rate(rating_asins, relevant_asins)
        price_rel = calculate_relevance_match_rate(price_asins, relevant_asins)
        
        print(f"  Agentic System:     {agentic_rel:.2%} relevant")
        print(f"  Rating Baseline:    {rating_rel:.2%} relevant")
        print(f"  Price Baseline:     {price_rel:.2%} relevant")
        
        # Store results
        query_result = {
            'query_id': query_id,
            'query_text': query_text,
            'agentic_asins': agentic_asins,
            'rating_asins': rating_asins,
            'price_asins': price_asins,
            'relevant_asins': relevant_asins,
            'agentic_relevance': agentic_rel,
            'rating_relevance': rating_rel,
            'price_relevance': price_rel
        }
        results['queries'].append(query_result)
        
        total_agentic_relevance += agentic_rel
        total_rating_relevance += rating_rel
        total_price_relevance += price_rel

    
    # Calculate aggregates
    num_queries = len(test_queries)
    results['aggregate']['agentic_avg_relevance'] = total_agentic_relevance / num_queries
    results['aggregate']['rating_baseline_avg_relevance'] = total_rating_relevance / num_queries
    results['aggregate']['price_baseline_avg_relevance'] = total_price_relevance / num_queries
    
    print(f"\n{'='*60}")
    print(f"BASELINE COMPARISON (k={k})")
    print(f"{'='*60}")
    print(f"Agentic System Avg:     {results['aggregate']['agentic_avg_relevance']:.2%}")
    print(f"Rating Baseline Avg:    {results['aggregate']['rating_baseline_avg_relevance']:.2%}")
    print(f"Price Baseline Avg:     {results['aggregate']['price_baseline_avg_relevance']:.2%}")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Compare against baselines')
    parser.add_argument('--test-file', type=str, default='eval_results/test_queries.json',
                        help='Path to test queries JSON file')
    parser.add_argument('--output-dir', type=str, default='eval_results',
                        help='Directory to save results')
    parser.add_argument('--k', type=int, default=5,
                        help='Number of top results to compare')
    
    args = parser.parse_args()
    
    # Load test queries
    print(f"Loading test queries from: {args.test_file}")
    test_queries = load_test_queries(args.test_file)
    print(f"Loaded {len(test_queries)} test queries\n")
    
    # Run comparison
    results = compare_systems(test_queries, k=args.k)
    
    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f'baseline_comparison_k{args.k}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")


if __name__ == '__main__':
    main()
