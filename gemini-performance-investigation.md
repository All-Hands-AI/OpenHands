# Gemini Performance Investigation

## Problem Statement
RooCode (VSCode extension) runs Gemini 2.5 Pro very fast, but OpenHands runs the same LLM extremely slowly on the same account. This suggests different API usage patterns or hyperparameters.

## Investigation Plan

### Phase 1: Analyze RooCode Implementation
- [ ] Find RooCode's Gemini API integration code
- [ ] Identify API endpoint, authentication method, and request structure
- [ ] Document hyperparameters (temperature, max_tokens, top_p, top_k, etc.)
- [ ] Check if it uses streaming vs non-streaming responses
- [ ] Look for any special configurations or optimizations

### Phase 2: Analyze OpenHands Implementation
- [ ] Find OpenHands' Gemini API integration code
- [ ] Identify API endpoint, authentication method, and request structure
- [ ] Document hyperparameters and compare with RooCode
- [ ] Check streaming configuration
- [ ] Look for any performance bottlenecks

### Phase 3: Compare and Identify Differences
- [ ] Create side-by-side comparison of API calls
- [ ] Identify key differences in:
  - Hyperparameters
  - Request structure
  - Authentication
  - Streaming configuration
  - Connection settings

### Phase 4: Implement Fixes
- [ ] Apply RooCode's successful configuration to OpenHands
- [ ] Test performance improvements
- [ ] Document changes and rationale

## Findings

### RooCode Analysis
- Location: workspace/roocode
- Status: ✅ COMPLETED

**Key Findings:**
1. **Library**: Uses `@google/genai` (Google's official Gemini SDK)
2. **API Method**: `client.models.generateContentStream()` for streaming
3. **Default Temperature**: 0 (line 75 in gemini.ts)
4. **Max Tokens**: Uses `modelMaxTokens` setting or model default
5. **Streaming**: Always uses streaming responses
6. **Reasoning Support**: Full support for thinking/reasoning tokens with `thinkingConfig`
7. **Prompt Caching**: Supports prompt caching with `cachedContentTokenCount`
8. **Request Structure**:
   - Uses `GenerateContentParameters` with `model`, `contents`, `config`
   - System instruction passed separately
   - Temperature defaults to 0
   - Supports reasoning budget and thinking tokens

**RooCode Configuration Details:**
- **Default Model**: `gemini-2.0-flash-001` (line 6 in gemini.ts)
- **Temperature**: Always 0 unless reasoning models require 1.0
- **Streaming**: Uses `generateContentStream()` method
- **Reasoning Config**:
  - For reasoning budget models: `{ thinkingBudget: reasoningBudget, includeThoughts: true }`
  - Reasoning budget capped at 80% of maxTokens, minimum 1024 tokens
- **Authentication**: Supports API key, Vertex AI with JSON credentials, or key file
- **Base URL**: Configurable via `googleGeminiBaseUrl` option
- **Token Counting**: Uses native `client.models.countTokens()` method
- **Cost Calculation**: Sophisticated tiered pricing calculation with cache read support

### OpenHands Analysis
- Location: openhands/llm/
- Status: ✅ COMPLETED

**Key Findings:**
1. **Library**: Uses LiteLLM (wrapper around multiple LLM providers)
2. **API Method**: `litellm.completion()` - generic completion interface
3. **Default Temperature**: 0.0 (line 69 in llm_config.py)
4. **Max Tokens**: Uses `max_output_tokens` config setting
5. **Streaming**: Configurable via `stream` parameter
6. **Reasoning Support**: Limited - supports `reasoning_effort` for some models
7. **Prompt Caching**: Enabled by default (`caching_prompt: true`)
8. **Request Structure**:
   - Uses LiteLLM's generic format (OpenAI-compatible)
   - All parameters passed through LiteLLM's abstraction layer
   - Special handling for Gemini tool calling limitations

**OpenHands Configuration Details:**
- **Default Model**: `claude-sonnet-4-20250514` (not Gemini)
- **Temperature**: 0.0 by default
- **Streaming**: Not always used (depends on caller)
- **LiteLLM Abstraction**: All calls go through LiteLLM's generic interface
- **Gemini-specific Issues**:
  - Tool calling limitations (removes default fields, limited format support)
  - Special error handling for "Response choices is less than 1"
  - Mock function calling for compatibility
- **Authentication**: Via `api_key` parameter
- **Base URL**: Configurable but uses LiteLLM's default endpoints
- **Token Counting**: Uses LiteLLM's generic token counting
- **Cost Calculation**: Uses LiteLLM's cost calculation

### Key Differences

**🔥 CRITICAL PERFORMANCE DIFFERENCES:**

1. **API Library**:
   - **RooCode**: Uses `@google/genai` (Google's official, optimized SDK)
   - **OpenHands**: Uses LiteLLM (generic wrapper with abstraction overhead)

2. **API Method**:
   - **RooCode**: Direct `client.models.generateContentStream()` call
   - **OpenHands**: Generic `litellm.completion()` with abstraction layers

3. **Streaming**:
   - **RooCode**: Always uses streaming (`generateContentStream`)
   - **OpenHands**: May or may not use streaming (depends on caller)

4. **Request Format**:
   - **RooCode**: Native Gemini format (`GenerateContentParameters`)
   - **OpenHands**: OpenAI-compatible format converted by LiteLLM

5. **Authentication & Endpoints**:
   - **RooCode**: Direct Google API endpoints with native auth
   - **OpenHands**: Through LiteLLM's endpoint abstraction

6. **Token Counting**:
   - **RooCode**: Native `client.models.countTokens()` method
   - **OpenHands**: LiteLLM's generic token counting (may be inaccurate)

7. **Reasoning Support**:
   - **RooCode**: Full native support with `thinkingConfig`
   - **OpenHands**: Limited support through LiteLLM abstraction

8. **Error Handling**:
   - **RooCode**: Native Gemini error handling
   - **OpenHands**: Multiple abstraction layers, special Gemini workarounds

### Proposed Fixes

**🎯 RECOMMENDED SOLUTION: Add Native Gemini Provider**

The performance difference is likely due to LiteLLM's abstraction overhead and suboptimal Gemini integration. We should add a native Gemini provider to OpenHands similar to RooCode's implementation.

**Implementation Plan:**

1. **Create Native Gemini LLM Class** (`openhands/llm/gemini.py`):
   - Use `@google/genai` library directly (or Python equivalent `google-generativeai`)
   - Implement streaming by default
   - Use native Gemini request format
   - Support reasoning/thinking tokens properly

2. **Update LLM Factory** (`openhands/llm/llm.py`):
   - Detect Gemini models and route to native provider
   - Fallback to LiteLLM for other models

3. **Configuration Changes**:
   - Add Gemini-specific config options
   - Support native authentication methods
   - Enable proper reasoning configuration

4. **Testing Strategy**:
   - Compare performance before/after
   - Ensure feature parity with LiteLLM version
   - Test with Gemini 2.5 Pro specifically

**Alternative Quick Fixes (if native provider is too complex):**

1. **Force Streaming**: Always use `stream=True` for Gemini models
2. **Optimize LiteLLM Config**:
   - Set `drop_params=False` for Gemini
   - Use native tool calling when possible
   - Configure proper reasoning parameters
3. **Direct Endpoint**: Use Google's direct API endpoints instead of LiteLLM's

## Next Steps

### ✅ COMPLETED
1. ✅ Explore RooCode codebase for Gemini integration
2. ✅ Explore OpenHands codebase for Gemini integration
3. ✅ Compare implementations
4. ✅ Identify root cause (LiteLLM abstraction overhead)

### ⚠️ INVESTIGATION UPDATE: DEEPER ANALYSIS NEEDED

**🎯 INITIAL FINDING: LiteLLM is NOT the bottleneck!**

**Performance Test Results (gemini-2.5-pro):**

| Method | Configuration | Duration | Overhead |
|--------|---------------|----------|----------|
| **Native Google API** | Streaming | 25.863s | Baseline |
| **Native Google API** | Non-streaming | 24.661s | Baseline |
| **LiteLLM** | OpenHands streaming | 25.680s | +0.8s (3%) |
| **LiteLLM** | OpenHands non-streaming | 26.564s | +1.9s (8%) |
| **LiteLLM** | Minimal config | 29.368s | +4.7s (19%) |

**🔍 Key Finding:** LiteLLM overhead is only 1-3 seconds (4-12%), NOT the 10x+ slowdown reported.

**🚨 CRITICAL DISCOVERY: User reports RooCode is FAST with gemini-2.5-pro!**

This contradicts our test results where ALL approaches with `gemini-2.5-pro` are slow (~25s).

**🔬 Thinking Budget Investigation:**

RooCode sets `thinkingConfig` for `gemini-2.5-pro` (marked as `requiredReasoningBudget: true`):
```typescript
// RooCode's approach
thinkingConfig: { thinkingBudget: 4096, includeThoughts: true }
```

**Thinking Budget Test Results:**
- No thinking config: 25.979s
- Thinking disabled: 26.113s
- Small thinking budget (1024): 23.724s ⭐ (fastest)

**🤔 HYPOTHESIS REFINEMENT:**
1. **Model selection was premature** - RooCode IS fast with `gemini-2.5-pro`
2. **Thinking budget helps slightly** - 2-3s improvement with small budget
3. **Missing configuration** - RooCode likely has other optimizations we haven't found
4. **Prompt differences** - RooCode may use different prompts/context

**📊 Test Suite Results:**
   ```bash
   # All tests show similar slow performance with gemini-2.5-pro
   python test_native_gemini.py     # 24-26s
   python test_litellm_performance.py  # 25-29s
   python test_openhands_litellm.py    # 25-31s
   python test_thinking_budget.py      # 23-26s
   ```

### 🛠️ CURRENT EXPERIMENT: Google's Gemini CLI Analysis

**🎯 NEW DISCOVERY: Google's Official Gemini CLI**

Found Google's official open-source Gemini CLI in workspace directory - perfect for investigation!

**✅ KEY FINDINGS:**
- **Uses native `@google/genai` SDK** (not LiteLLM) - direct comparison baseline
- **Has built-in debug mode**: `--debug` flag for detailed logging
- **Supports gemini-2.5-pro**: Default model is `gemini-2.5-pro`
- **Easy to modify**: Open source, can add custom logging if needed

**🔬 INVESTIGATION PLAN:**
1. **Test Gemini CLI performance** with `gemini-2.5-pro` in debug mode
2. **Compare timing** with our test results (~25s)
3. **Analyze debug output** to see exact API configuration
4. **If needed**: Add custom logging to capture full request details
5. **Compare** with RooCode's LiteLLM proxy approach

**Commands to test:**
```bash
cd workspace/gemini-cli
./bundle/gemini.js --model gemini-2.5-pro --debug --prompt "Hello, test message"
```

**Expected Benefits:**
- Direct performance comparison with native Google SDK
- Detailed debug output showing API configuration
- Easier to modify than browser extension
- Clear baseline for "fast" vs "slow" performance

**Status:** ✅ **BREAKTHROUGH ACHIEVED!**

**🚨 CRITICAL DISCOVERY:**
- **Gemini CLI with gemini-2.5-pro: 2.6-5.2 seconds** ⚡
- **Our test implementations: ~25 seconds** 🐌
- **Performance gap: 5-10x faster!**

**Test Results:**
```bash
# Test 1: Simple greeting
time ./bundle/gemini.js --model gemini-2.5-pro --debug --prompt "Hello, test message"
# Result: 2.589s

# Test 2: Code generation
time ./bundle/gemini.js --model gemini-2.5-pro --debug --prompt "Write Python function"
# Result: 5.188s
```

**✅ CONFIRMED:** Google's official CLI achieves the fast performance user reported!

### 🎯 SECONDARY APPROACH: RooCode Extension Analysis

**Plan B:** If Gemini CLI shows similar slow performance, investigate RooCode directly:
1. **Find RooCode extension directory** in Windsurf
2. **Add console.log statements** to capture LiteLLM proxy requests
3. **Compare exact request payloads** with our test implementations

### 🎯 CURRENT STATUS

**✅ CONFIRMED FINDINGS:**
- **LiteLLM abstraction overhead is minimal** (only 1-3s difference, 4-12%)
- **All our test approaches show ~25s with gemini-2.5-pro** (Native API, LiteLLM, thinking budget)
- **RooCode uses LiteLLM proxy** (`llm-proxy.eval.all-hands.dev`) - NOT Google's direct API
- **Thinking budget provides small improvement** (2-3s faster) but not dramatic speedup

**🎯 BREAKTHROUGH CONFIRMED:**
Google's official Gemini CLI achieves **2.6-5.2s** with `gemini-2.5-pro` - validating user's fast performance reports!

**🔍 NEXT PHASE:**
Analyze what makes Gemini CLI fast vs our slow implementations (~25s) to identify the optimization gap.

## 🚀 HTTP Request Analysis - BREAKTHROUGH ACHIEVED

**MAJOR SUCCESS**: Successfully captured full HTTP request details from Gemini CLI!

### Corrected Understanding
- **CORRECTION**: `play.googleapis.com` requests were telemetry logging, not actual API calls
- **ACTUAL API**: Gemini CLI uses same `generativelanguage.googleapis.com` endpoint as our implementations
- **REAL DIFFERENCE**: Configuration and request structure differences, not endpoint

### Captured HTTP Requests

#### Request 1: Model Test/Initialization (972ms)
```bash
🚀 FETCH REQUEST: {
  method: 'POST',
  url: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent',
  headers: {
    'Content-Type': 'application/json',
    'x-goog-api-key': 'AIz...'
  }
}
📤 REQUEST BODY: {
  "contents":[{"parts":[{"text":"test"}]}],
  "generationConfig":{
    "maxOutputTokens":1,
    "temperature":0,
    "topK":1,
    "thinkingConfig":{
      "thinkingBudget":128,
      "includeThoughts":false
    }
  }
}
```

#### Request 2: Actual Generation (3714ms)
```bash
🚀 FETCH REQUEST: {
  method: 'POST',
  url: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:streamGenerateContent?alt=sse',
  headers: {
    'User-Agent': 'GeminiCLI/0.1.13 (darwin; arm64)',
    'x-goog-api-client': 'google-genai-sdk/1.9.0 gl-node/v23.11.0',
    'Content-Type': 'application/json',
    'x-goog-api-key': 'AIz...'
  }
}
```

### Critical Configuration Differences

1. **Thinking Budget**: Gemini CLI uses `thinkingBudget: 128` with `includeThoughts: false`
2. **Streaming**: Uses `:streamGenerateContent?alt=sse` for streaming responses
3. **SDK Headers**: Includes specific SDK identification headers:
   - `User-Agent: GeminiCLI/0.1.13 (darwin; arm64)`
   - `x-goog-api-client: google-genai-sdk/1.9.0 gl-node/v23.11.0`
4. **Request Structure**: Two-phase approach (test + generation)
5. **Model Initialization**: Separate test request with minimal output

### Performance Analysis
- **Total Time**: ~21s (similar to our implementations)
- **Request 1**: 972ms (model initialization)
- **Request 2**: 3714ms (actual generation)
- **Remaining Time**: ~16s (likely model processing/thinking time)

### Key Insights
1. **Same Endpoint**: No infrastructure advantage from different endpoints
2. **Configuration Focus**: Differences are in request configuration, not infrastructure
3. **Streaming vs Non-streaming**: Gemini CLI uses streaming, we use non-streaming
4. **SDK Headers**: Proper SDK identification may affect routing/prioritization
5. **Two-phase Approach**: Separate initialization may optimize subsequent requests

### Next Steps
1. **Test streaming vs non-streaming** in our implementations
2. **Add proper SDK headers** to match Gemini CLI
3. **Implement two-phase approach** (test + generation)
4. **Compare thinking budget settings** (128 vs our current settings)
5. **Analyze why total time is still ~21s** despite fast individual requests
