VERIFIED_OPENAI_MODELS = [
    'gpt-5-2025-08-07',
    'gpt-5-mini-2025-08-07',
    'o4-mini',
    'gpt-4o',
    'gpt-4o-mini',
    'gpt-4-32k',
    'gpt-4.1',
    'gpt-4.1-2025-04-14',
    'o1-mini',
    'o3',
    'codex-mini-latest',
]

VERIFIED_ANTHROPIC_MODELS = [
    'claude-sonnet-4-20250514',
    'claude-opus-4-20250514',
    'claude-opus-4-1-20250805',
    'claude-3-7-sonnet-20250219',
    'claude-3-sonnet-20240229',
    'claude-3-opus-20240229',
    'claude-3-haiku-20240307',
    'claude-3-5-haiku-20241022',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-sonnet-20240620',
    'claude-2.1',
    'claude-2',
]

VERIFIED_MISTRAL_MODELS = [
    'devstral-small-2505',
    'devstral-small-2507',
    'devstral-medium-2507',
]

VERIFIED_OPENHANDS_MODELS = [
    'claude-sonnet-4-20250514',
    'gpt-5-2025-08-07',
    'gpt-5-mini-2025-08-07',
    'claude-opus-4-20250514',
    'claude-opus-4-1-20250805',
    'devstral-small-2507',
    'devstral-medium-2507',
    'o3',
    'o4-mini',
    'gemini-2.5-pro',
    'kimi-k2-0711-preview',
    'qwen3-coder-480b',
]


VERIFIED_PROVIDERS = {
    'openhands': VERIFIED_OPENHANDS_MODELS,
    'anthropic': VERIFIED_ANTHROPIC_MODELS,
    'openai': VERIFIED_OPENAI_MODELS,
    'mistral': VERIFIED_MISTRAL_MODELS,
}
