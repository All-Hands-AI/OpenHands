# Line-Level Overlap Calculation Explanation

## For instance: django__django-12774

### The Calculation Formula

The line-level overlap is calculated as:

```
line_level_overlap = (generated_hits + golden_hits) / (total_generated_lines + total_golden_lines)
```

Where:
- **generated_hits**: Number of generated patch lines that fall within ±3 lines of any golden patch line
- **golden_hits**: Number of golden patch lines that fall within ±3 lines of any generated patch line
- **total_generated_lines**: Total number of lines modified by the generated patch
- **total_golden_lines**: Total number of lines modified by the golden patch

### Actual Numbers for django__django-12774

- Generated hits: **6 lines** (lines 692-697 in django/db/models/query.py)
- Golden hits: **9 lines** (lines 692-700 in django/db/models/query.py)
- Total generated lines: **585 lines** (8 lines in query.py + 577 lines in new test files)
- Total golden lines: **11 lines** (only in query.py)

**Result**: (6 + 9) / (585 + 11) = 15 / 596 = **0.0252** (2.52%)

### Why Is It So Low?

The line-level overlap is very low (2.52%) despite the fix being in the correct location because:

1. **Test File Inflation**: The generated patch creates multiple new test files:
   - `test_constraint_in_bulk.py` (111 lines)
   - `test_direct.py` (88 lines)
   - `test_my_fix.py` (165 lines)
   - `test_reproduction.py` (126 lines)
   - `test_reproduction_simple.py` (89 lines)
   - Total: **579 test lines**

2. **Golden Patch Simplicity**: The golden patch only modifies `django/db/models/query.py` with 11 lines of changes

3. **Dilution Effect**: Even though:
   - File-level Jaccard: **1.0** (both patches modify query.py)
   - Function-level Jaccard: **1.0** (both patches modify the same function)
   - The line-level metric is diluted by the 579 test lines that have no correspondence in the golden patch

### Breakdown by File

**Generated Patch:**
- `django/db/models/query.py`: 8 changed lines (6 adds, 2 removes)
- `test_constraint_in_bulk.py`: 111 new lines
- `test_direct.py`: 88 new lines
- `test_my_fix.py`: 165 new lines
- `test_reproduction.py`: 126 new lines
- `test_reproduction_simple.py`: 89 new lines

**Golden Patch:**
- `django/db/models/query.py`: 11 changed lines (10 adds, 1 remove)

### Line-Level Overlap Details

In `django/db/models/query.py`:
- Lines **692-697** from generated patch overlap with golden patch (within ±3 line range)
- Lines **692-700** from golden patch overlap with generated patch (within ±3 line range)
- This gives **15 overlapping line instances** out of **596 total modified lines**

### Interpretation

This demonstrates that **line-level metrics are sensitive to extra code** (like test files) even when the core fix is correctly localized. The file-level and function-level metrics (both 1.0) are better indicators of localization correctness in this case.

### Recommendations

For better localization assessment:
1. **File-level Jaccard**: Best for high-level localization (same files modified?)
2. **Function-level Jaccard**: Best for code structure localization (same functions/classes?)
3. **Line-level overlap**: Best for precise change localization, but **sensitive to volume** of changes

Consider filtering out test files or using weighted metrics if test file creation is a common pattern in generated patches.
