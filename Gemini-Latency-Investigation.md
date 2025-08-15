# Gemini 2.5 Pro Latency Investigation

Goal: Identify and fix extreme latency seen when using Gemini 2.5 Pro via OpenHands (through LiteLLM), which is not observed when using the official Gemini CLI.

This doc tracks status, observations, experiments, and next steps.

## Status
- Cloned official Gemini CLI repository alongside OpenHands:
  - Repo: https://github.com/google-gemini/gemini-cli
  - Local path: /workspace/gemini-cli
- Located OpenHands -> LiteLLM call path:
  - openhands/llm/llm.py wraps litellm.completion and sets parameters
  - Model-specific behavior (Gemini 2.5 Pro) is handled in this wrapper and by LiteLLM’s Gemini mapper
- Found LiteLLM Gemini implementation on disk:
  - litellm/llms/vertex_ai/gemini/vertex_and_google_ai_studio_gemini.py
- Prepared a Python harness (experiments/gemini_latency_harness.py) to send comparable prompts via OpenHands wrapper for timing and logging. A small Node harness for @google/genai can be added if needed.

## Initial Observations (CLI vs OpenHands)
- Gemini CLI (TS, @google/genai):
  - Uses GoogleGenAI and calls models.generateContent()
  - Default generation config includes:
    - temperature: 0
    - topP: 1
    - For models starting with gemini-2.5, adds thinkingConfig: { includeThoughts: true }
  - System instructions are passed as systemInstruction (not as a chat message)
  - Tools are set via functionDeclarations and sent as tools: [{ functionDeclarations: [...] }]
  - Adds a custom User-Agent header (GeminiCLI/<version>)

- OpenHands (Python, LiteLLM):
  - Calls litellm.completion with kwargs assembled in openhands/llm/llm.py
  - For gemini-2.5-pro specifically, current mapping does:
    - If reasoning_effort in {None, "low", "none"}:
      - Adds thinking = { budget_tokens: 128 }
      - Sets allowed_openai_params = ["thinking"] (LiteLLM-internal allowance)
      - Drops reasoning_effort
    - Removes temperature and top_p when reasoning effort models are detected (to mirror OpenAI-like reasoning behavior)
  - System message is included as a chat message; LiteLLM is expected to translate to systemInstruction. The exact mapping may differ from the CLI.
  - Tools are passed as OpenAI-style tools/JSON schema; LiteLLM maps these to Gemini functionDeclarations.

Potential differences to test for latency impact:
- Thinking config
  - CLI: includeThoughts: true with no explicit budget
  - OpenHands: budget_tokens: 128 (no include flag)
- Tool calling defaults
  - tool_choice defaults to "auto" via LiteLLM mapping (FunctionCallingConfig mode AUTO), same as CLI behavior. But we should confirm.
- System prompt handling
  - CLI uses systemInstruction field; OpenHands uses a system chat message that LiteLLM should map. We should verify payloads.
- LiteLLM global modify_params and other transformations
  - OpenHands sets litellm.modify_params = True by default; confirm if this adds overhead or changes payload.
- Parallel tool calls behavior and any added params by LiteLLM

## Experiments Plan
1) Baseline single-turn, no tools
- Prompt: simple user message
- Measure latency in OpenHands via experiments/gemini_latency_harness.py
- Measure latency in Gemini CLI (or minimal @google/genai Node script) with the same API key and model

2) Tool-calling turn
- Provide one simple function (e.g., sum two numbers)
- Ask the model to call the function
- Compare latencies

3) Parameter sweeps in OpenHands wrapper
- thinking variants:
  - no thinking (send nothing)
  - includeThoughts only (no budget)
  - budget_tokens = 128 (current)
  - reasoning_effort = low|medium|high mapped via LiteLLM’s reasoning mapping (which sets thinkingConfig under the hood)
- system prompt placement
  - system chat message vs. explicitly setting systemInstruction (requires adjustment/patch)
- LiteLLM flags
  - modify_params True vs False
  - drop_params True vs False (should be True anyway to avoid errors)
- tool_choice
  - explicit "auto" vs omit vs "none" (when testing tools)

4) Capture exact outgoing request bodies
- Enable OpenHands log_completions to write args/kwargs per call
- Monkey-patch LiteLLM Gemini client to log final request JSON to a file for comparison against @google/genai requests

## Hypotheses for Latency
- Request shape differences cause the Gemini backend to take a slower path (e.g., tool config, system message mapping, or thinking config)
- LiteLLM adds parameters (or retries/transformations) that increase effective latency
- System prompt as a chat message vs systemInstruction affects planning/thinking durations
- Parallel tool calling or internal AFC (automatic function calling) behavior differs

## Next Steps (needs API access)
- Provide GEMINI_API_KEY (or GOOGLE_API_KEY with vertex settings) as environment variables
- Run the harness:
  - OpenHands harness: poetry run python experiments/gemini_latency_harness.py --model gemini/gemini-2.5-pro
  - Node harness using @google/genai (optional, we can add a script if needed)
- Compare latencies across sweeps and record in this doc

## Proposed Fix Directions (to validate by experiment)
- Align OpenHands thinking config with CLI:
  - Option A: send thinkingConfig includeThoughts: true, no explicit budget (let server default)
  - Option B: allow users to toggle thinking behavior via config; ensure reasoning_effort = "none" truly disables thinking (currently it still sets budget 128)
- Ensure tool configuration mirrors CLI’s shape closely (functionDeclarations array within tools, auto mode)
- Consider passing systemInstruction explicitly for Gemini models instead of a system chat message (pending LiteLLM support and tests)
- If a specific LiteLLM transform adds latency, monkey-patch around it in OpenHands

## Artifacts
- Python harness: experiments/gemini_latency_harness.py (measures OpenHands path latency; logs args/kwargs and response)
- This doc: Gemini-Latency-Investigation.md

## Open Questions / Needs
- API credentials to run live tests
- Whether to commit monkey patches vs behind a feature flag
- Exact request payload produced by @google/genai for our tested scenarios (we can log via a small Node script)

## Changes Implemented
- OPENHANDS_GEMINI_CLI_COMPAT flag in OpenHands LLM to send thinking={type:'enabled'} and retain temperature/top_p for gemini-2.5-pro to mimic CLI.
- experiments/gemini_latency_harness.py to benchmark OpenHands path.

## TODO
- Add minimal Node @google/genai script for parity tests and to log raw request payloads.
- Monkey-patch LiteLLM to log final JSON request body for Gemini generateContent (temporary) to compare shapes.
