#!/usr/bin/env python3
"""
Precision@k and Recall@k Evaluation Script

This script evaluates the agentic shopping assistant using standard
information retrieval metrics: Precision@k and Recall@k.

Usage:
    python evaluate_precision_recall.py --output-dir eval_results
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

# Add parent directory to path to import buying_guide module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.buying_guide.app.session import run_agentic_session


def load_test_queries(test_file: str) -> List[Dict]:
    """Load test queries from JSON file."""
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_queries']


def run_system_for_query(query_text: str, top_k: int = 5) -> List[str]:
    """
    Run the agentic system for a single query and return top-k ASINs.
    
    Returns:
        List of ASINs in ranked order
    """
    try:
        result = run_agentic_session(query_text, top_k=top_k)
        products = result.get('products', [])
        asins = [p['asin'] for p in products if 'asin' in p]
        return asins
    except Exception as e:
        print(f"Error running query '{query_text}': {e}")
        return []


def calculate_precision_recall(
    retrieved_asins: List[str],
    relevant_asins: List[str],
    k: int = 5
) -> Tuple[float, float]:
    """
    Calculate Precision@k and Recall@k.
    
    Args:
        retrieved_asins: List of retrieved ASINs (top-k)
        relevant_asins: List of ground truth relevant ASINs
        k: Cutoff value
    
    Returns:
        Tuple of (precision, recall)
    """
    if not retrieved_asins or not relevant_asins:
        return 0.0, 0.0
    
    # Take only top-k retrieved items
    retrieved_k = set(retrieved_asins[:k])
    relevant_set = set(relevant_asins)
    
    # Calculate intersection
    relevant_retrieved = retrieved_k.intersection(relevant_set)
    
    # Precision@k = |retrieved ∩ relevant| / k
    precision = len(relevant_retrieved) / k if k > 0 else 0.0
    
    # Recall@k = |retrieved ∩ relevant| / |relevant|
    recall = len(relevant_retrieved) / len(relevant_set) if len(relevant_set) > 0 else 0.0
    
    return precision, recall


def evaluate_all_queries(test_queries: List[Dict], k: int = 5) -> Dict:
    """
    Evaluate all test queries and compute average metrics.
    
    Returns:
        Dictionary with results for each query and aggregated metrics
    """
    results = {
        'k': k,
        'queries': [],
        'aggregate': {
            'avg_precision': 0.0,
            'avg_recall': 0.0,
            'num_queries': len(test_queries)
        }
    }
    
    total_precision = 0.0
    total_recall = 0.0
    
    for query_data in test_queries:
        query_id = query_data['query_id']
        query_text = query_data['query_text']
        relevant_asins = query_data['relevant_asins']
        
        print(f"\nEvaluating Query {query_id}: {query_text}")
        
        # Run system
        retrieved_asins = run_system_for_query(query_text, top_k=k)
        
        # Calculate metrics
        precision, recall = calculate_precision_recall(
            retrieved_asins, 
            relevant_asins, 
            k=k
        )
        
        print(f"  Retrieved: {retrieved_asins}")
        print(f"  Relevant:  {relevant_asins}")
        print(f"  Precision@{k}: {precision:.3f}")
        print(f"  Recall@{k}: {recall:.3f}")
        
        # Store results
        query_result = {
            'query_id': query_id,
            'query_text': query_text,
            'retrieved_asins': retrieved_asins,
            'relevant_asins': relevant_asins,
            'precision': precision,
            'recall': recall,
            'num_relevant_retrieved': len(set(retrieved_asins[:k]).intersection(set(relevant_asins)))
        }
        results['queries'].append(query_result)
        
        total_precision += precision
        total_recall += recall
    
    # Calculate aggregates
    num_queries = len(test_queries)
    results['aggregate']['avg_precision'] = total_precision / num_queries if num_queries > 0 else 0.0
    results['aggregate']['avg_recall'] = total_recall / num_queries if num_queries > 0 else 0.0
    
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS (k={k})")
    print(f"{'='*60}")
    print(f"Average Precision@{k}: {results['aggregate']['avg_precision']:.3f}")
    print(f"Average Recall@{k}:    {results['aggregate']['avg_recall']:.3f}")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Evaluate Precision@k and Recall@k')
    parser.add_argument('--test-file', type=str, default='eval_results/test_queries.json',
                        help='Path to test queries JSON file')
    parser.add_argument('--output-dir', type=str, default='eval_results',
                        help='Directory to save results')
    parser.add_argument('--k', type=int, default=5,
                        help='k value for Precision@k and Recall@k')
    
    args = parser.parse_args()
    
    # Load test queries
    print(f"Loading test queries from: {args.test_file}")
    test_queries = load_test_queries(args.test_file)
    print(f"Loaded {len(test_queries)} test queries\n")
    
    # Run evaluation
    results = evaluate_all_queries(test_queries, k=args.k)
    
    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f'precision_recall_k{args.k}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")


if __name__ == '__main__':
    main()
