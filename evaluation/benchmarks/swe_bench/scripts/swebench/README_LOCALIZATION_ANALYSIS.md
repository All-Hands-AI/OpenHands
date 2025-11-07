# Patch Localization Analysis Tool

This tool analyzes the localization correctness of generated patches from SWE-bench evaluation outputs by comparing them with golden patches from the dataset.

## Overview

The tool calculates three levels of localization similarity:

1. **File-level Jaccard**: Whether patches modify the same files
2. **Function-level Jaccard**: Whether patches modify the same functions/classes
3. **Line-level overlap**: Whether modified lines overlap within ±3 line ranges

**Note**: Test files are automatically excluded from the generated patches in line-level calculations to avoid dilution from agent-created test files.

## Requirements

- Python 3.7+
- Required packages:
  ```bash
  pip install datasets
  ```

## Usage

### Using the Shell Script (Recommended)

```bash
./run_localization_analysis.sh <eval_output_dir> [options]
```

**Options:**
- `--dataset NAME`: Dataset name (default: `princeton-nlp/SWE-bench_Verified`)
- `--split SPLIT`: Dataset split (default: `test`)
- `--output FILE`: Output JSON file path (default: `<eval_output_dir>/localization_analysis.json`)
- `--limit N`: Limit number of instances to analyze (useful for testing)

**Examples:**

```bash
# Analyze all instances
./run_localization_analysis.sh /path/to/eval_outputs

# Test with limited instances
./run_localization_analysis.sh /path/to/eval_outputs --limit 10

# Specify custom output file
./run_localization_analysis.sh /path/to/eval_outputs --output my_results.json

# Use SWE-bench Lite dataset
./run_localization_analysis.sh /path/to/eval_outputs --dataset princeton-nlp/SWE-bench_Lite
```

### Using Python Directly

```bash
python3 analyze_patch_localization.py <eval_output_dir> [options]
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "summary": {
    "total_instances": 100,
    "successful": 95,
    "failed": 5,
    "average_file_level_jaccard": 0.75,
    "average_function_level_jaccard": 0.65,
    "average_line_level_overlap": 0.58,
    "file_level_distribution": {...},
    "function_level_distribution": {...},
    "line_level_distribution": {...}
  },
  "results": [
    {
      "instance_id": "django__django-12774",
      "success": true,
      "file_level_jaccard": 1.0,
      "function_level_jaccard": 1.0,
      "line_level_overlap": 0.8824,
      "generated_files": ["django/db/models/query.py"],
      "generated_non_test_files": ["django/db/models/query.py"],
      "generated_test_files": [],
      "golden_files": ["django/db/models/query.py"],
      "generated_locations": [...],
      "golden_locations": [...],
      "num_generated_locations": 1,
      "num_golden_locations": 1,
      "num_function_level_intersection": 1,
      "error": null
    },
    ...
  ]
}
```

## How It Works

### 1. File-level Similarity

Compares the set of files modified by both patches using Jaccard similarity:

```
Jaccard = |Generated_Files ∩ Golden_Files| / |Generated_Files ∪ Golden_Files|
```

### 2. Function-level Similarity

Uses Abstract Syntax Tree (AST) analysis to extract modified functions/classes, then compares:

```
Jaccard = |Generated_Functions ∩ Golden_Functions| / |Generated_Functions ∪ Golden_Functions|
```

For Python files, the tool identifies:
- Functions modified at any level
- Class methods modified
- Global code changes (with ±3 line context)

### 3. Line-level Overlap

Calculates overlap of modified line ranges with ±3 line context:

```
Overlap = (Generated_Hits + Golden_Hits) / (Total_Generated_Lines + Total_Golden_Lines)
```

Where:
- **Generated_Hits**: Generated patch lines falling within ±3 lines of golden patch lines
- **Golden_Hits**: Golden patch lines falling within ±3 lines of generated patch lines

**Important**: Test files are filtered out from generated patches to avoid dilution.

### Test File Filtering

The tool automatically identifies and excludes test files based on:
- Directory names: `test/`, `tests/`, `__tests__/`, `test_utils/`
- File name patterns: `test_*.py`, `*_test.py`, `test.py`, `tests.py`
- Path containing `test` or `_test`

This ensures that agent-created test files don't artificially lower the line-level metrics.

## Example Output

```
============================================================
SUMMARY
============================================================
Total instances: 500
Successful analyses: 485
Failed analyses: 15

Average File-level Jaccard: 0.7823
Average Function-level Jaccard: 0.6891
Average Line-level overlap: 0.6245

File-level Jaccard distribution:
  0.0-0.2: 45 (9.3%)
  0.2-0.4: 62 (12.8%)
  0.4-0.6: 78 (16.1%)
  0.6-0.8: 115 (23.7%)
  0.8-1.0: 185 (38.1%)

Function-level Jaccard distribution:
  0.0-0.2: 58 (12.0%)
  0.2-0.4: 72 (14.8%)
  0.4-0.6: 95 (19.6%)
  0.6-0.8: 125 (25.8%)
  0.8-1.0: 135 (27.8%)

Line-level overlap distribution:
  0.0-0.2: 75 (15.5%)
  0.2-0.4: 88 (18.1%)
  0.4-0.6: 102 (21.0%)
  0.6-0.8: 115 (23.7%)
  0.8-1.0: 105 (21.6%)
```

## Interpreting Results

- **File-level = 1.0**: Perfect file localization (same files modified)
- **Function-level = 1.0**: Perfect function localization (same functions modified)
- **Line-level > 0.8**: High precision in exact line modifications
- **Line-level < 0.3**: Many extra/missing changes, but may still be correct at function level

**Best Practice**: Use all three metrics together for comprehensive analysis:
- File-level for coarse-grained localization
- Function-level for structural localization
- Line-level for fine-grained change precision

## Troubleshooting

### "datasets library not found"
```bash
pip install datasets
```

### "Failed to clone/checkout repository"
- Check internet connection
- Verify GitHub access
- Some repositories may require authentication

### "Generated patch not found"
- Ensure the eval_output_dir contains `eval_outputs/<instance_id>/patch.diff` files
- Check that the evaluation has completed

## Performance Notes

- The tool clones repositories as needed, which can be slow
- Use `--limit` for testing before full runs
- Repositories are cleaned up after each instance to save disk space
- Typical speed: ~30-60 seconds per instance (depending on repository size)

## Location

- Python script: `evaluate/benchmarks/swe_bench/scripts/swebench/analyze_patch_localization.py`
- Shell script: `evaluate/benchmarks/swe_bench/scripts/swebench/run_localization_analysis.sh`
