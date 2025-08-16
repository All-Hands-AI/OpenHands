# Reasoning Content in OpenHands

This document explains how provider-native reasoning content ("reasoning_content") is surfaced in OpenHands, how it is serialized on the event stream, how the frontend displays it, and what must not be sent back to the LLM on subsequent rounds.

Scope
- Source of truth: LiteLLM `ModelResponse`/`choices[0].message`
- Event model: Thought dataclass (backend) normalized to wire `args.thought` (string) + optional `args.reasoning_content` (string)
- FE: Render reasoning_content above thought when present; do not duplicate
- Memory: Do not send reasoning_content back to the model

What we receive from LiteLLM
- LiteLLM normalizes provider outputs and, for reasoning models, exposes the model’s chain-of-thought via:
  - message.reasoning_content: string (preferred, standardized field)
  - message.thinking_blocks: array (Anthropic-specific; optional; we currently use only string content when present)
  - Some providers may also place reasoning under message.reasoning or message.thinking
  - In multi-part content (list), some providers emit blocks with type="reasoning" or type="thinking" with a text field

References (LiteLLM docs)
- Thinking / Reasoning Content: https://docs.litellm.ai/docs/reasoning_content
- xAI provider example with reasoning_content: https://docs.litellm.ai/docs/providers/xai
- Note: Some providers do not expose reasoning (e.g., OpenAI o-series). Reasoning may be absent.

Backend data model and serialization
- Thought is now a dataclass with fields:
  - text: str — the human-readable thought
  - reasoning_content: Optional[str] — provider-native chain-of-thought
- Serialization (event_to_dict):
  - We flatten the Thought for wire-compatibility:
    - args.thought is always the text string
    - args.reasoning_content is included only when present
- Deserialization (action_from_dict):
  - Accepts legacy forms: args.thought as string, or args.thought as object with {text, reasoning_content}
  - Also accepts a separate args.reasoning_content string and folds it into Thought

Where we extract reasoning_content
- conversation_memory.py (AgentFinish, tool-calling path):
  - Extracts provider reasoning, in this order:
    1) message.reasoning_content, message.reasoning, message.thinking (first-party fields)
    2) content blocks where type in {"reasoning", "thinking"}
  - Joins multiple reasoning fragments with newlines
  - Stores on action.thought.reasoning_content
- function_calling.py (CodeAct/Loc/Readonly):
  - When tool calls are present, we collect:
    - text thought from message.content (string or "text" blocks)
    - reasoning from message.reasoning_content / message.reasoning / message.thinking
    - reasoning from content blocks of type reasoning/thinking
  - Then we call combine_thought(action, thought, reasoning_content)

Frontend behavior
- Types: All actions with thought also include optional reasoning_content?: string in args
- Rendering:
  - event-message.tsx shows reasoning_content above thought for agent actions (when present), without double-rendering
  - get-action-content.ts shows reasoning_content above thought for Think actions (when present)
  - Assistant/user message chat bubbles still render their message content; for AssistantMessageAction, we do not add reasoning_content to the LLM conversation

Backwards compatibility
- Wire compatibility is preserved:
  - We still emit args.thought (string)
  - args.reasoning_content is optional and omitted if empty
  - action_from_dict accepts both legacy string and new object forms for thought
- UI compatibility:
  - If reasoning_content is absent, UI behaves as before
  - If only reasoning_content is present (rare), we render it alone

Important constraints: do NOT send reasoning_content back to the LLM
- Reasoning tokens are provider-private and many APIs explicitly forbid sending them back.
- In OpenHands, ConversationMemory prepares the messages for the next LLM call. We ensure that:
  - We never include reasoning_content in user/assistant messages we pass to the model
  - We only include the public thought text as needed for tools/UX, not the private reasoning_content
- Code pointers:
  - conversation_memory.process_events/_process_action constructs Message objects; no code adds reasoning_content to any Message
  - event_to_dict includes reasoning_content only in the event stream payload sent to the client; it is not repackaged into LLM input

Coding practices notes
- Prefer direct attribute access for LiteLLM responses (choices[0].message) instead of getattr when the object is guaranteed by the SDK
- Be permissive but simple when extracting reasoning: check standardized fields first, then block lists; join with newlines
- Keep Thought as the single place holding reasoning_content on the backend; keep wire format simple (string thought + optional reasoning_content)
- On the frontend, avoid duplicate rendering; prefer rc then thought

Examples
- Backend: flattening in event_to_dict
  - Input (server memory): thought=Thought(text="X", reasoning_content="R")
  - Wire JSON: { args: { thought: "X", reasoning_content: "R" } }
- Deserialization: action_from_dict
  - Accepts { args: { thought: "X" } }
  - Accepts { args: { thought: { text: "X", reasoning_content: "R" } } }
  - Accepts { args: { thought: "X", reasoning_content: "R" } }

Open questions / caveats
- Some providers stream reasoning in deltas; we currently collect after each round from the aggregated message
- Not all providers expose reasoning; field may be null
