import argparse
import json
import os
import time
from typing import Any

from openhands.core.config.llm_config import LLMConfig
from openhands.llm.llm import LLM


def make_messages(prompt: str, system: str | None = None) -> list[dict[str, Any]]:
    msgs: list[dict[str, Any]] = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})
    return msgs


def make_tools(include: bool) -> list[dict[str, Any]] | None:
    if not include:
        return None
    # Simple echo tool for function-calling path
    return [
        {
            'type': 'function',
            'function': {
                'name': 'echo',
                'description': 'Echo the provided text',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'text': {'type': 'string'},
                    },
                    'required': ['text'],
                },
            },
        }
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Measure Gemini latency via OpenHands -> LiteLLM'
    )
    parser.add_argument(
        '--model', default=os.getenv('OPENHANDS_MODEL', 'gemini/gemini-2.5-pro')
    )
    parser.add_argument(
        '--api-key', default=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    )
    parser.add_argument('--base-url', default=os.getenv('OPENHANDS_BASE_URL'))
    parser.add_argument('--reasoning', default=os.getenv('OPENHANDS_REASONING'))
    parser.add_argument(
        '--temperature',
        type=float,
        default=float(os.getenv('OPENHANDS_TEMPERATURE', '0')),
    )
    parser.add_argument(
        '--top-p', type=float, default=float(os.getenv('OPENHANDS_TOP_P', '1'))
    )
    parser.add_argument(
        '--max-output-tokens',
        type=int,
        default=int(os.getenv('OPENHANDS_MAX_OUTPUT_TOKENS', '1024')),
    )
    parser.add_argument('--with-tools', action='store_true')
    parser.add_argument(
        '--prompt',
        default="Say hello and then call the echo function with text='hello' if tools exist.",
    )
    parser.add_argument('--system', default='You are a helpful assistant.')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument(
        '--cli-compat',
        action='store_true',
        help='Set OPENHANDS_GEMINI_CLI_COMPAT=1 for this run',
    )
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit(
            'Please set --api-key or GEMINI_API_KEY/GOOGLE_API_KEY env var'
        )

    if args.cli_compat:
        os.environ['OPENHANDS_GEMINI_CLI_COMPAT'] = '1'

    cfg = LLMConfig(
        model=args.model,
        api_key=args.api_key,  # type: ignore[arg-type]
        base_url=args.base_url,
        temperature=args.temperature,
        top_p=args.top_p,
        max_output_tokens=args.max_output_tokens,
        reasoning_effort=args.reasoning,
        log_completions=True,
    )

    llm = LLM(cfg)

    tools = make_tools(args.with_tools)
    messages = make_messages(args.prompt, args.system)

    latencies: list[float] = []
    for i in range(args.runs):
        t0 = time.time()
        resp = llm.completion(messages=messages, **({'tools': tools} if tools else {}))
        dt = time.time() - t0
        latencies.append(dt)
        choice = resp.get('choices', [{}])[0]
        text = choice.get('message', {}).get('content') or choice.get(
            'message', {}
        ).get('text')
        print(f'Run {i + 1}: latency={dt:.3f}s text={str(text)[:120]!r}')

    if latencies:
        print(
            json.dumps(
                {
                    'model': args.model,
                    'runs': len(latencies),
                    'avg_latency_sec': sum(latencies) / len(latencies),
                    'min_latency_sec': min(latencies),
                    'max_latency_sec': max(latencies),
                    'cli_compat': bool(args.cli_compat),
                    'with_tools': bool(args.with_tools),
                },
                indent=2,
            )
        )


if __name__ == '__main__':
    main()
