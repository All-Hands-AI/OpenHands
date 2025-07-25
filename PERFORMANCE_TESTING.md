# Gemini Performance Testing Suite

This suite helps isolate the root cause of Gemini 2.5 Pro performance issues in OpenHands vs RooCode.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install litellm google-generativeai
   ```

2. **Set your API key:**
   ```bash
   export GOOGLE_API_KEY=your_key_here
   ```

3. **Run comprehensive tests:**
   ```bash
   python run_performance_tests.py
   ```

## Individual Tests

### 1. `test_litellm_performance.py`
Tests pure LiteLLM with different configurations:
- RooCode-like config (streaming, temp=0)
- OpenHands default config (no streaming)
- OpenHands with streaming
- Minimal config

**Purpose:** Determine if LiteLLM itself is slow or if it's configuration-dependent.

### 2. `test_openhands_litellm.py`
Tests LiteLLM exactly as OpenHands calls it:
- Uses OpenHands' exact configuration
- Tests streaming vs non-streaming
- Tests with/without reasoning effort

**Purpose:** Isolate if OpenHands-specific configurations cause slowdown.

### 3. `test_native_gemini.py`
Tests native Google Generative AI library (like RooCode):
- Direct Google API calls
- Native streaming and non-streaming
- No abstraction layers

**Purpose:** Establish baseline performance with native Google SDK.

## What We're Testing

**Key Hypotheses:**
1. **LiteLLM Overhead:** LiteLLM abstraction adds significant latency
2. **Streaming Impact:** Non-streaming requests are much slower
3. **Configuration Issues:** OpenHands has suboptimal default parameters
4. **Format Conversion:** OpenAI-to-Gemini format conversion adds overhead

**Key Metrics:**
- Total response time
- Time to first chunk (streaming)
- Response quality/length consistency

## Expected Outcomes

**If LiteLLM is the problem:**
- Native Google API will be significantly faster
- All LiteLLM configs will be similarly slow

**If it's configuration:**
- Some LiteLLM configs will be fast (matching native)
- OpenHands-style calls will be slower than optimized LiteLLM

**If it's streaming:**
- Streaming will be much faster than non-streaming
- Time-to-first-chunk will be very low for streaming

## Results Analysis

The test runner will:
1. Run all tests automatically
2. Extract performance metrics
3. Compare results across approaches
4. Save detailed results to `performance_test_results.json`
5. Provide actionable conclusions

## Next Steps Based on Results

**If native is much faster:**
→ Implement native Gemini provider for OpenHands

**If LiteLLM can be fast with right config:**
→ Fix OpenHands' LiteLLM configuration

**If streaming makes the difference:**
→ Force streaming for Gemini models in OpenHands

**If it's specific parameters:**
→ Identify and fix the problematic parameters
