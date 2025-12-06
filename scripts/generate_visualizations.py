#!/usr/bin/env python3
"""
Generate Evaluation Visualizations

Creates bar charts and tables for evaluation metrics.

Usage:
    python generate_visualizations.py
"""

import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np
import os

def load_results():
    """Load evaluation results from JSON files."""
    with open('eval_results/precision_recall_k5.json', 'r') as f:
        pr_data = json.load(f)
    
    with open('eval_results/constraint_coverage_k5.json', 'r') as f:
        cc_data = json.load(f)
    
    with open('eval_results/baseline_comparison_k5.json', 'r') as f:
        bc_data = json.load(f)
    
    return pr_data, cc_data, bc_data


def create_precision_recall_chart(pr_data):
    """Create bar chart for Precision@5 and Recall@5."""
    avg_precision = pr_data['aggregate']['avg_precision']
    avg_recall = pr_data['aggregate']['avg_recall']
    
    metrics = ['Precision@5', 'Recall@5']
    values = [avg_precision, avg_recall]
    
    plt.figure(figsize=(8, 6))
    colors = ['#4CAF50', '#2196F3']
    bars = plt.bar(metrics, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{val:.2%}',
                 ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    plt.ylabel('Score', fontsize=12, fontweight='bold')
    plt.title('Precision@5 and Recall@5 Metrics', fontsize=14, fontweight='bold')
    plt.ylim(0, 1.0)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    output_path = 'eval_results/precision_recall_chart.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Created: {output_path}")
    plt.close()


def create_constraint_coverage_chart(cc_data):
    """Create bar chart for constraint coverage by feature type."""
    feature_coverage = cc_data['aggregate']['feature_coverage_by_type']
    budget_coverage = cc_data['aggregate']['avg_budget_coverage']
    
    # Add budget to features
    all_features = {'Budget': budget_coverage, **feature_coverage}
    
    features = list(all_features.keys())
    coverages = list(all_features.values())
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(features)))
    bars = plt.barh(features, coverages, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
# Add value labels
    for bar, val in zip(bars, coverages):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                 f'{val:.0%}',
                 ha='left', va='center', fontweight='bold', fontsize=11, 
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    plt.xlabel('Coverage (%)', fontsize=12, fontweight='bold')
    plt.title('Constraint Coverage by Type', fontsize=14, fontweight='bold')
    plt.xlim(0, 1.0)
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    output_path = 'eval_results/constraint_coverage_chart.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Created: {output_path}")
    plt.close()


def create_baseline_comparison_chart(bc_data):
    """Create grouped bar chart comparing agentic system vs baselines."""
    agentic_rel = bc_data['aggregate']['agentic_avg_relevance']
    rating_rel = bc_data['aggregate']['rating_baseline_avg_relevance']
    price_rel = bc_data['aggregate']['price_baseline_avg_relevance']
    
    methods = ['Agentic\nSystem', 'Rating-Only\nBaseline', 'Price-Only\nBaseline']
    relevances = [agentic_rel, rating_rel, price_rel]
    
    plt.figure(figsize=(10, 6))
    colors = ['#FF5722', '#9E9E9E', '#9E9E9E']
    bars = plt.bar(methods, relevances, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, val in zip(bars, relevances):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{val:.0%}',
                 ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    plt.ylabel('Average Relevance', fontsize=12, fontweight='bold')
    plt.title('Agentic System vs Naive Baselines', fontsize=14, fontweight='bold')
    plt.ylim(0, 1.0)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    output_path = 'eval_results/baseline_comparison_chart.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Created: {output_path}")
    plt.close()


def main():
    print("Loading evaluation results...")
    pr_data, cc_data, bc_data = load_results()
    
    print("\nGenerating visualizations...")
    create_precision_recall_chart(pr_data)
    create_constraint_coverage_chart(cc_data)
    create_baseline_comparison_chart(bc_data)
    
    print("\nAll visualizations created successfully!")


if __name__ == '__main__':
    main()
