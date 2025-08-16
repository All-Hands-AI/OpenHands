# Consolidated Gemini Performance Test Suite

This document describes the consolidated and deduplicated test suite for investigating Gemini 2.5 Pro performance issues in OpenHands.

## 📁 Test Files Overview

### 1. `test_thinking_budget.py` - **PRIMARY THINKING/REASONING TEST**
**Purpose**: Primary test for thinking budget and reasoning effort configurations
**Features**:
- Tests old vs new Google Generative AI APIs
- Compares thinking budget configurations (128, 1024, 2048, 4096 tokens)
- Tests reasoning_effort parameters via LiteLLM
- Includes direct REST API calls for comparison
- **User Preference**: This is the main file for thinking/reasoning tests

### 2. `test_litellm_comprehensive.py` - **COMPREHENSIVE LITELLM TEST**
**Purpose**: Consolidated LiteLLM performance testing (replaces test_litellm_performance.py + test_openhands_litellm.py)
**Features**:
- Basic LiteLLM configurations (streaming, temperature, etc.)
- OpenHands-style configuration and calls
- Reasoning effort and thinking budget parameters
- Comprehensive performance analysis and comparison
- **Consolidation**: Combines functionality from 2 previous files

### 3. `test_native_gemini.py` - **NATIVE GOOGLE API TEST**
**Purpose**: Tests native Google Generative AI library (like RooCode uses)
**Features**:
- Direct Google API calls without LiteLLM abstraction
- Streaming and non-streaming tests
- Performance comparison baseline
- **Baseline**: Shows optimal performance without middleware

### 4. `test_openhands_gemini_fix.py` - **OPENHANDS FIX VERIFICATION**
**Purpose**: Tests the actual OpenHands Gemini performance fix implementation
**Features**:
- Tests OpenHands with optimized thinking budget configuration
- Verifies 2.5x speedup (from ~25s to ~10s)
- Configuration inspection and validation
- **Implementation**: Tests the actual fix we deployed

### 5. `run_performance_tests.py` - **TEST ORCHESTRATOR**
**Purpose**: Runs all tests in sequence and provides comprehensive analysis
**Features**:
- Dependency checking
- Sequential test execution
- Performance metrics extraction
- Comparative analysis across all test types
- **Orchestrator**: Runs all tests and provides summary

## 🗑️ Removed Files (Redundant)

### Removed: `quick_test.py`
- **Reason**: Very basic test, functionality covered by `test_native_gemini.py`
- **Redundancy**: Simple native API test already in comprehensive native test

### Removed: `test_litellm_performance.py`
- **Reason**: Merged into `test_litellm_comprehensive.py`
- **Redundancy**: Basic LiteLLM configurations now in comprehensive test

### Removed: `test_openhands_litellm.py`
- **Reason**: Merged into `test_litellm_comprehensive.py`
- **Redundancy**: OpenHands-style calls now in comprehensive test

## 🎯 Test Suite Organization

```
Performance Testing Hierarchy:
├── run_performance_tests.py (Orchestrator)
├── test_thinking_budget.py (Primary thinking/reasoning)
├── test_litellm_comprehensive.py (All LiteLLM scenarios)
├── test_native_gemini.py (Baseline performance)
└── test_openhands_gemini_fix.py (Fix verification)
```

## 🚀 Usage

### Run Individual Tests:
```bash
# Primary thinking/reasoning test
python test_thinking_budget.py

# Comprehensive LiteLLM test
python test_litellm_comprehensive.py

# Native API baseline
python test_native_gemini.py

# OpenHands fix verification
python test_openhands_gemini_fix.py
```

### Run Complete Suite:
```bash
# Run all tests with analysis
python run_performance_tests.py
```

## 📊 Test Coverage

| Test Aspect | Primary Test File | Coverage |
|-------------|------------------|----------|
| **Thinking Budget** | `test_thinking_budget.py` | ✅ Complete |
| **Reasoning Effort** | `test_thinking_budget.py` | ✅ Complete |
| **LiteLLM Performance** | `test_litellm_comprehensive.py` | ✅ Complete |
| **OpenHands Style** | `test_litellm_comprehensive.py` | ✅ Complete |
| **Native API Baseline** | `test_native_gemini.py` | ✅ Complete |
| **Fix Verification** | `test_openhands_gemini_fix.py` | ✅ Complete |
| **Streaming vs Non-streaming** | All files | ✅ Complete |
| **Parameter Variations** | All files | ✅ Complete |

## 🎉 Benefits of Consolidation

1. **Reduced Redundancy**: Eliminated duplicate test logic across 3 files
2. **Better Organization**: Clear separation of concerns by test purpose
3. **Easier Maintenance**: Single comprehensive test instead of multiple overlapping ones
4. **User Preference**: `test_thinking_budget.py` as primary thinking/reasoning test
5. **Complete Coverage**: All original functionality preserved and enhanced

## 🔧 Dependencies

- `litellm` - For LiteLLM testing
- `google-generativeai` - For old Google API
- `google-genai` - For new Google API with thinking budget
- `openhands` - For OpenHands fix testing

All dependencies are checked by `run_performance_tests.py` before execution.
