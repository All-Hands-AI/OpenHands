import json
from typing import Iterable

from openhands.resolver.resolver_output import ResolverOutput


def load_all_resolver_outputs(output_jsonl: str) -> Iterable[ResolverOutput]:
    with open(output_jsonl, 'r') as f:
        for line in f:
            yield ResolverOutput.model_validate(json.loads(line))


def load_single_resolver_output(output_jsonl: str, issue_number: int) -> ResolverOutput:
    for resolver_output in load_all_resolver_outputs(output_jsonl):
        if resolver_output.issue.number == issue_number:
            return resolver_output
    raise ValueError(f'Issue number {issue_number} not found in {output_jsonl}')
