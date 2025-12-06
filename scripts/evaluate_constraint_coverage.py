#!/usr/bin/env python3
"""
Constraint Coverage Evaluation Script

This script evaluates how well the agentic system's top-k results
satisfy the user's constraints (budget, features, use case).

Usage:
    python evaluate_constraint_coverage.py --output-dir eval_results
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Set
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.buying_guide.app.session import run_agentic_session


def load_test_queries(test_file: str) -> List[Dict]:
    """Load test queries from JSON file."""
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_queries']


def check_budget_constraint(product: Dict, constraint: Dict) -> bool:
    """Check if product satisfies budget constraint."""
    price = product.get('price')
    if price is None:
        return False
    
    budget_max = constraint.get('budget_max')
    budget_min = constraint.get('budget_min', 0)
    
    if budget_max is not None and price > budget_max:
        return False
    if budget_min is not None and price < budget_min:
        return False
        
    return True


def check_feature_constraints(product: Dict, required_features: List[str]) -> Dict[str, bool]:
    """
    Check which features are present in the product.
    
    Returns:
        Dictionary mapping feature to whether it's satisfied
    """
    # Get product title and text for keyword matching
    title = (product.get('title') or '').lower()
    
    feature_checks = {}
    
    for feature in required_features:
        feature_lower = feature.lower()
        
        # Simple keyword matching
        if feature_lower in ['wireless', 'bluetooth']:
            satisfied = 'wireless' in title or 'bluetooth' in title
        elif feature_lower in ['wired']:
            satisfied = 'wired' in title or ('wireless' not in title and 'bluetooth' not in title)
        elif feature_lower in ['noise cancelling', 'noise canceling', 'anc']:
            satisfied = 'noise cancel' in title or 'anc' in title
        elif feature_lower in ['waterproof', 'water resistant', 'sweatproof']:
            satisfied = 'waterproof' in title or 'water' in title or 'sweat' in title or 'ipx' in title
        elif feature_lower in ['bass', 'extra bass']:
            satisfied = 'bass' in title
        elif feature_lower in ['microphone', 'mic']:
            satisfied = 'mic' in title or 'microphone' in title
        elif feature_lower in ['foldable', 'folding']:
            satisfied = 'fold' in title
        elif feature_lower in ['usb-c', 'usb c', 'type c']:
            satisfied = 'usb' in title or 'type c' in title
       elif feature_lower in ['detachable cable', 'replaceable cable']:
            satisfied = 'detachable' in title or 'replaceable' in title
        else:
            # Generic keyword match
            satisfied = feature_lower in title
        
        feature_checks[feature] = satisfied
    
    return feature_checks


def evaluate_constraint_coverage(
    products: List[Dict],
    constraints: Dict
) -> Dict:
    """
    Evaluate how well products satisfy constraints.
    
    Returns:
        Dictionary with coverage metrics
    """
    if not products:
        return {
            'budget_coverage': 0.0,
            'feature_coverage': {},
            'overall_coverage': 0.0
        }
    
    # Count products satisfying budget
    budget_satisfied = 0
    for p in products:
        if check_budget_constraint(p, constraints):
            budget_satisfied += 1
    
    budget_coverage = budget_satisfied / len(products)
    
    # Check feature coverage
    required_features = constraints.get('features', [])
    feature_coverage = {}
    
    if required_features:
        for feature in required_features:
            satisfied_count = 0
            for p in products:
                feature_checks = check_feature_constraints(p, [feature])
                if feature_checks.get(feature, False):
                    satisfied_count += 1
            feature_coverage[feature] = satisfied_count / len(products)
    
    # Overall coverage (average of budget and all features)
    all_coverages = [budget_coverage] + list(feature_coverage.values())
    overall_coverage = sum(all_coverages) / len(all_coverages) if all_coverages else 0.0
    
    return {
        'budget_coverage': budget_coverage,
        'feature_coverage': feature_coverage,
        'overall_coverage': overall_coverage,
        'num_products': len(products)
    }


def evaluate_all_queries(test_queries: List[Dict], k: int = 5) -> Dict:
    """
    Evaluate constraint coverage for all test queries.
    
    Returns:
        Dictionary with results for each query and aggregated metrics
    """
    results = {
        'k': k,
        'queries': [],
        'aggregate': {
            'avg_budget_coverage': 0.0,
            'avg_overall_coverage': 0.0,
            'feature_coverage_by_type': {}
        }
    }
    
    total_budget_coverage = 0.0
    total_overall_coverage = 0.0
    feature_coverages = {}
    
    for query_data in test_queries:
        query_id = query_data['query_id']
        query_text = query_data['query_text']
        constraints = query_data.get('constraints', {})
        
        print(f"\nEvaluating Query {query_id}: {query_text}")
        
        # Run system
        try:
            result = run_agentic_session(query_text, top_k=k)
            products = result.get('products', [])
        except Exception as e:
            print(f"  Error: {e}")
            products = []
        
        # Evaluate constraints
        coverage = evaluate_constraint_coverage(products, constraints)
        
        print(f"  Budget Coverage: {coverage['budget_coverage']:.2%}")
        if coverage['feature_coverage']:
            print(f"  Feature Coverage:")
            for feature, cov in coverage['feature_coverage'].items():
                print(f"    - {feature}: {cov:.2%}")
        print(f"  Overall Coverage: {coverage['overall_coverage']:.2%}")
        
        # Store results
        query_result = {
            'query_id': query_id,
            'query_text': query_text,
            'constraints': constraints,
            'coverage': coverage
        }
        results['queries'].append(query_result)
        
        total_budget_coverage += coverage['budget_coverage']
        total_overall_coverage += coverage['overall_coverage']
        
        # Aggregate feature coverages
        for feature, cov in coverage['feature_coverage'].items():
            if feature not in feature_coverages:
                feature_coverages[feature] = []
            feature_coverages[feature].append(cov)
    
    # Calculate aggregates
    num_queries = len(test_queries)
    results['aggregate']['avg_budget_coverage'] = total_budget_coverage / num_queries if num_queries > 0 else 0.0
    results['aggregate']['avg_overall_coverage'] = total_overall_coverage / num_queries if num_queries > 0 else 0.0
    
    # Average feature coverages
    for feature, covs in feature_coverages.items():
        results['aggregate']['feature_coverage_by_type'][feature] = sum(covs) / len(covs)
    
    print(f"\n{'='*60}")
    print(f"OVERALL CONSTRAINT COVERAGE (k={k})")
    print(f"{'='*60}")
    print(f"Average Budget Coverage:  {results['aggregate']['avg_budget_coverage']:.2%}")
    print(f"Average Overall Coverage: {results['aggregate']['avg_overall_coverage']:.2%}")
    if results['aggregate']['feature_coverage_by_type']:
        print(f"\nFeature Coverage by Type:")
        for feature, cov in results['aggregate']['feature_coverage_by_type'].items():
            print(f"  - {feature}: {cov:.2%}")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Evaluate Constraint Coverage')
    parser.add_argument('--test-file', type=str, default='eval_results/test_queries.json',
                        help='Path to test queries JSON file')
    parser.add_argument('--output-dir', type=str, default='eval_results',
                        help='Directory to save results')
    parser.add_argument('--k', type=int, default=5,
                        help='Number of top results to evaluate')
    
    args = parser.parse_args()
    
    # Load test queries
    print(f"Loading test queries from: {args.test_file}")
    test_queries = load_test_queries(args.test_file)
    print(f"Loaded {len(test_queries)} test queries\n")
    
    # Run evaluation
    results = evaluate_all_queries(test_queries, k=args.k)
    
    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f'constraint_coverage_k{args.k}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")


if __name__ == '__main__':
    main()
