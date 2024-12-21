import json
import os
import argparse
from collections import defaultdict

def load_jsonl(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def calculate_accuracy(results):
    correct = sum(1 for result in results if result['test_result']['result'])
    total = len(results)
    return correct / total if total > 0 else 0

def evaluate_results(output_file):
    results = load_jsonl(output_file)
    accuracy = calculate_accuracy(results)
    
    # Calculate accuracy by year
    accuracy_by_year = defaultdict(lambda: {'correct': 0, 'total': 0})
    for result in results:
        year = result['metadata']['details']['Year']
        accuracy_by_year[year]['total'] += 1
        if result['test_result']['result']:
            accuracy_by_year[year]['correct'] += 1
    
    accuracy_by_year = {year: data['correct'] / data['total'] for year, data in accuracy_by_year.items()}
    
    return {
        'overall_accuracy': accuracy,
        'accuracy_by_year': accuracy_by_year,
        'total_problems': len(results)
    }

def main():
    parser = argparse.ArgumentParser(description='Evaluate AIME inference results')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory containing output.jsonl')
    args = parser.parse_args()

    output_file = os.path.join(args.output_dir, 'output.jsonl')
    if not os.path.exists(output_file):
        print(f"Error: {output_file} does not exist.")
        return

    results = evaluate_results(output_file)
    
    print(f"Overall Accuracy: {results['overall_accuracy']:.2%}")
    print(f"Total Problems Evaluated: {results['total_problems']}")
    print("\nAccuracy by Year:")
    for year, acc in sorted(results['accuracy_by_year'].items()):
        print(f"{year}: {acc:.2%}")

if __name__ == "__main__":
    main()