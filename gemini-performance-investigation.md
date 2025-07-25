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

### 🛠️ NEXT STEPS

**🔍 IMMEDIATE INVESTIGATION NEEDED:**

1. **Verify RooCode's actual performance** with `gemini-2.5-pro`
   - Test RooCode directly with same prompt
   - Measure actual response times
   - Compare with our test results

2. **Identify missing RooCode optimizations:**
   - Analyze RooCode's exact API calls (network inspection)
   - Check for additional parameters we missed
   - Compare prompt formatting and context

3. **Test LiteLLM with thinking budget:**
   - Implement thinking budget in LiteLLM calls
   - Test if LiteLLM supports `thinkingConfig` parameter
   - Compare with native API performance

### 🎯 CURRENT STATUS

**The performance issue is NOT primarily LiteLLM abstraction overhead (only 1-3s difference).**

**However, we haven't yet identified why RooCode is fast with `gemini-2.5-pro` while our tests are slow.**

**Possible remaining factors:**
- Different prompt structure/length
- Additional API parameters we haven't discovered
- Different API endpoints or versions
- Caching or other optimizations

**CRITICAL:** Need to verify user's claim that RooCode is fast with `gemini-2.5-pro` before proceeding with solutions.
