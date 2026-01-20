import json
import os
import sys
from collections import defaultdict
from rag_engine import IndustrialRAG

# 设置颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def evaluate_baseline():
    """
    Evaluate the baseline retrieval performance (Vector Search Only)
    using the Golden Dataset.
    Metric: Recall@K (Does the ground truth doc appear in the Top-K retrieved docs?)
    """
    
    # 1. Load Golden Dataset
    dataset_path = 'golden_dataset.json'
    if not os.path.exists(dataset_path):
        print(f"{RED}Error: Golden dataset not found at {dataset_path}{RESET}")
        return

    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"{BOLD}Starting Baseline Evaluation on first 10 of {len(dataset)} test cases...{RESET}")
    print("-" * 60)

    # 2. Initialize RAG Engine
    rag = IndustrialRAG()
    
    # Metrics
    hits_at_5 = 0
    total = 0 # Initialize total to 0 for dynamic counting
    category_stats = defaultdict(lambda: {'total': 0, 'hits': 0})
    missed_cases = []

    # 3. Run Evaluation (LIMIT 10)
    for i, item in enumerate(dataset[:10]): # Limit to first 10 cases
        question = item['question']
        ground_truth_doc = item['ground_truth_doc']
        category = item.get('category', 'Unknown')
        
        total += 1 # Increment total for each processed case
        category_stats[category]['total'] += 1
        
        # Perform Retrieval (Baseline: Vector Search -> Parent Child Expansion)
        # We retrieve top_k=5 chunks, which leads to 1~5 parent documents.
        # This effectively measures: "Is the correct document triggered by the top 5 chunks?"
        retrieved_docs = rag.retrieve(question, top_k=5)
        
        # Extract unique filenames found
        found_filenames = set(doc.metadata.get('filename') for doc in retrieved_docs)
        
        # Check Hit
        if ground_truth_doc in found_filenames:
            hits_at_5 += 1
            category_stats[category]['hits'] += 1
            print(f"[{i+1}/{total}] {GREEN}HIT {RESET} | Q: {question[:30]}... -> Found: {ground_truth_doc}")
        else:
            print(f"[{i+1}/{total}] {RED}MISS{RESET} | Q: {question[:30]}... -> Expected: {ground_truth_doc}")
            # print(f"    Found: {list(found_filenames)}")
            missed_cases.append({
                "id": item['id'],
                "question": question,
                "expected": ground_truth_doc,
                "found": list(found_filenames)
            })

    # 4. Report Results
    print("-" * 60)
    print(f"{BOLD}Evaluation Report (Rerank: Search 50 -> Rerank -> Top 5){RESET}")
    print(f"Total Cases: {total}")
    print(f"Recall@5:    {hits_at_5}/{total} ({hits_at_5/total:.1%})")
    
    print("\n[Breakdown by Category]")
    for cat, stats in category_stats.items():
        acc = stats['hits'] / stats['total']
        print(f"  - {cat}: {stats['hits']}/{stats['total']} ({acc:.1%})")

    if missed_cases:
        print("\n[Missed Cases for Review - Top 3]")
        for m in missed_cases[:3]:
            print(f"  Q: {m['question']}")
            print(f"  Exp: {m['expected']}")
            print(f"  Got: {m['found']}")
            print("-" * 20)
            
    # Save detailed report
    report_filename = 'evaluation_rerank_report.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        report = {
            "metric": "Recall@5",
            "score": hits_at_5/total,
            "missed_cases": missed_cases
        }
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed report saved to {report_filename}")

if __name__ == "__main__":
    evaluate_baseline()
