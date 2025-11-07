#!/usr/bin/env python3
"""Debug script to understand line-level overlap calculation."""

import re
from collections import defaultdict

from datasets import load_dataset


def parse_patch(patch_text):
    """Parse a unified diff patch and return modified files with their line changes."""
    file_changes = defaultdict(list)
    current_file = None
    current_line_old = 0
    current_line_new = 0

    lines = patch_text.split('\n')

    for line in lines:
        # File header
        if line.startswith('--- ') or line.startswith('+++ '):
            if line.startswith('+++ '):
                # Extract file path
                file_path = line[4:].split('\t')[0].strip()
                # Remove 'b/' prefix if present
                if file_path.startswith('b/'):
                    file_path = file_path[2:]
                if file_path and file_path != '/dev/null':
                    current_file = file_path
            continue

        # Hunk header
        if line.startswith('@@'):
            match = re.match(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
            if match:
                current_line_old = int(match.group(1))
                current_line_new = int(match.group(2))
            continue

        if current_file is None:
            continue

        # Change lines
        if line.startswith('+') and not line.startswith('+++'):
            file_changes[current_file].append((current_line_new, 'add'))
            current_line_new += 1
        elif line.startswith('-') and not line.startswith('---'):
            file_changes[current_file].append((current_line_old, 'remove'))
            current_line_old += 1
        elif line.startswith(' '):
            current_line_old += 1
            current_line_new += 1

    return dict(file_changes)


# Read actual patches
with open(
    '/home/v-murongma/code/OpenHands/evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/Qwen3-Coder-30B-A3B-Instruct_maxiter_100_N_v0.59.0-no-hint-run_1/eval_outputs/django__django-12774/patch.diff',
    'r',
) as f:
    generated_patch = f.read()


dataset = load_dataset('princeton-nlp/SWE-bench_Verified', split='test')
for item in dataset:
    if item['instance_id'] == 'django__django-12774':
        golden_patch = item['patch']
        break

gen_changes = parse_patch(generated_patch)
gold_changes = parse_patch(golden_patch)

print('Generated patch changes:')
for file_path, changes in gen_changes.items():
    if file_path.endswith('.py'):  # Only show Python files
        print(f'  {file_path}:')
        for line_num, change_type in changes:
            print(f'    Line {line_num}: {change_type}')

print('\nGolden patch changes:')
for file_path, changes in gold_changes.items():
    if file_path.endswith('.py'):
        print(f'  {file_path}:')
        for line_num, change_type in changes:
            print(f'    Line {line_num}: {change_type}')


# Now calculate line-level overlap
def get_line_ranges(file_changes):
    line_sets = defaultdict(set)
    line_ranges = defaultdict(list)

    for file_path, changes in file_changes.items():
        for line_num, change_type in changes:
            if change_type in ['add', 'remove']:
                line_sets[file_path].add(line_num)

        if line_sets[file_path]:
            sorted_lines = sorted(line_sets[file_path])
            ranges = []
            for line in sorted_lines:
                ranges.append((max(1, line - 3), line + 3))
            line_ranges[file_path] = ranges

    return line_sets, line_ranges


gen_lines, gen_ranges = get_line_ranges(gen_changes)
gold_lines, gold_ranges = get_line_ranges(gold_changes)

print('\n' + '=' * 60)
print('Generated line sets and ranges (Python files only):')
for file_path in gen_lines:
    if file_path.endswith('.py'):
        print(f'  {file_path}:')
        print(f'    Modified lines: {sorted(gen_lines[file_path])}')
        print(f'    Ranges (±3 lines): {gen_ranges[file_path][:5]}...')  # Show first 5

print('\nGolden line sets and ranges (Python files only):')
for file_path in gold_lines:
    if file_path.endswith('.py'):
        print(f'  {file_path}:')
        print(f'    Modified lines: {sorted(gold_lines[file_path])}')
        print(f'    Ranges (±3 lines): {gold_ranges[file_path]}')

# Calculate hits
generated_hits = set()
golden_hits = set()

for file_path in gen_lines:
    if file_path in gold_ranges:
        for gen_line in gen_lines[file_path]:
            for gold_start, gold_end in gold_ranges[file_path]:
                if gold_start <= gen_line <= gold_end:
                    generated_hits.add((file_path, gen_line))
                    break

for file_path in gold_lines:
    if file_path in gen_ranges:
        for gold_line in gold_lines[file_path]:
            for gen_start, gen_end in gen_ranges[file_path]:
                if gen_start <= gold_line <= gen_end:
                    golden_hits.add((file_path, gold_line))
                    break

print('\n' + '=' * 60)
print('Overlap calculation:')
print(f'Generated lines that fall in golden ranges: {len(generated_hits)}')
if generated_hits:
    print(f'  {sorted(list(generated_hits)[:10])}')
print(f'Golden lines that fall in generated ranges: {len(golden_hits)}')
if golden_hits:
    print(f'  {sorted(list(golden_hits)[:10])}')

all_gen_lines = {(f, line) for f in gen_lines for line in gen_lines[f]}
all_gold_lines = {(f, line) for f in gold_lines for line in gold_lines[f]}

print(f'\nTotal generated modified lines: {len(all_gen_lines)}')
print(f'Total golden modified lines: {len(all_gold_lines)}')

intersection = len(generated_hits) + len(golden_hits)
total_lines = len(all_gen_lines) + len(all_gold_lines)

overlap = intersection / total_lines if total_lines > 0 else 1.0

print(f'\nLine-level overlap = {intersection} / {total_lines} = {overlap:.6f}')
print(f'This equals: {overlap:.10f}')

print('\n' + '=' * 60)
print('EXPLANATION:')
print('=' * 60)
print("""
The line-level overlap is calculated as:
  (generated_hits + golden_hits) / (total_generated_lines + total_golden_lines)

Where:
- generated_hits = number of generated patch lines that fall within ±3 lines of any golden patch line
- golden_hits = number of golden patch lines that fall within ±3 lines of any generated patch line
- total_generated_lines = total number of lines modified by generated patch
- total_golden_lines = total number of lines modified by golden patch

The overlap is low because:
1. The generated patch includes many NEW test files (test_constraint_in_bulk.py, etc.)
   with hundreds of lines that don't exist in the golden patch
2. These extra lines dilute the overlap ratio even though the core fix is in the right location
3. The golden patch ONLY modifies django/db/models/query.py
4. The generated patch modifies query.py PLUS adds test files

So even though the fix location is correct (same function), the additional test files
make the line-level metric very low.
""")
