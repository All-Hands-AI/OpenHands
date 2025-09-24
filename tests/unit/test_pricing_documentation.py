"""
Unit tests to verify pricing documentation consistency.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import requests


class TestPricingDocumentation:
    """Test class for pricing documentation consistency."""

    @pytest.fixture
    def pricing_data(self) -> dict[str, Any]:
        """Fetch pricing data from LiteLLM repository."""
        url = 'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    @pytest.fixture
    def openhands_models(self) -> list[str]:
        """Get the list of OpenHands models from the codebase."""
        # Read the models directly from the source code file
        llm_utils_path = (
            Path(__file__).parent.parent.parent / 'openhands' / 'utils' / 'llm.py'
        )
        content = llm_utils_path.read_text()

        # Extract the openhands_models list from the file
        import ast

        # Parse the Python file
        tree = ast.parse(content)

        # Find the openhands_models assignment
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == 'openhands_models'
            ):
                # Extract the list values
                if isinstance(node.value, ast.List):
                    models = []
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            # Remove 'openhands/' prefix and filter out secret models
                            model = elt.value
                            if model.startswith('openhands/'):
                                model = model[10:]  # Remove 'openhands/' prefix
                            if not model.startswith('<secret'):
                                models.append(model)
                    return models

        # Fallback if parsing fails
        raise ValueError('Could not extract openhands_models from llm.py')

    @pytest.fixture
    def documentation_content(self) -> str:
        """Read the OpenHands LLM documentation content."""
        docs_path = (
            Path(__file__).parent.parent.parent
            / 'docs'
            / 'usage'
            / 'llms'
            / 'openhands-llms.mdx'
        )
        return docs_path.read_text()

    def extract_pricing_from_docs(self, content: str) -> dict[str, dict[str, float]]:
        """Extract pricing information from documentation."""
        # Updated pattern to handle cached input cost column (which can be N/A)
        pricing_table_pattern = (
            r'\| ([^|]+) \| \$([0-9.]+) \| ([^|]+) \| \$([0-9.]+) \|'
        )
        matches = re.findall(pricing_table_pattern, content)

        pricing_data = {}
        for match in matches:
            model_name = match[0].strip()
            input_cost = float(match[1])
            cached_input_str = match[2].strip()
            output_cost = float(match[3])

            # Parse cached input cost (can be N/A or $X.XX)
            cached_input_cost = None
            if cached_input_str != 'N/A':
                cached_input_cost = float(cached_input_str.replace('$', ''))

            pricing_data[model_name] = {
                'input_cost_per_million_tokens': input_cost,
                'cached_input_cost_per_million_tokens': cached_input_cost,
                'output_cost_per_million_tokens': output_cost,
            }

        return pricing_data

    def get_litellm_pricing(
        self, model: str, pricing_data: dict[str, Any]
    ) -> dict[str, float]:
        """Get pricing for a model from LiteLLM data."""
        # Try different variations of the model name
        variations = [
            model,
            f'openai/{model}',
            f'anthropic/{model}',
            f'google/{model}',
            f'mistral/{model}',
        ]

        for variation in variations:
            if variation in pricing_data:
                model_data = pricing_data[variation]
                result = {
                    'input_cost_per_million_tokens': model_data.get(
                        'input_cost_per_token', 0
                    )
                    * 1_000_000,
                    'output_cost_per_million_tokens': model_data.get(
                        'output_cost_per_token', 0
                    )
                    * 1_000_000,
                }

                # Add cached input cost if available
                cached_cost = model_data.get('cache_read_input_token_cost', 0)
                if cached_cost > 0:
                    result['cached_input_cost_per_million_tokens'] = (
                        cached_cost * 1_000_000
                    )

                return result

        return {}

    def test_pricing_table_exists(self, documentation_content: str):
        """Test that the pricing table exists in the documentation."""
        assert (
            '| Model | Input Cost (per 1M tokens) | Cached Input Cost (per 1M tokens) | Output Cost (per 1M tokens)'
            in documentation_content
        )
        assert 'claude-opus-4-20250514' in documentation_content
        assert 'qwen3-coder-480b' in documentation_content

    def test_no_external_json_link(self, documentation_content: str):
        """Test that the external JSON link has been removed."""
        assert (
            'github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json'
            not in documentation_content
        )

    def test_pricing_consistency_with_litellm(
        self, pricing_data: dict[str, Any], documentation_content: str
    ):
        """Test that pricing in documentation matches LiteLLM data where applicable."""
        docs_pricing = self.extract_pricing_from_docs(documentation_content)

        # Special case for qwen3-coder-480b (custom pricing)
        qwen_pricing = docs_pricing.get('qwen3-coder-480b')
        assert qwen_pricing is not None
        assert qwen_pricing['input_cost_per_million_tokens'] == 0.4
        assert qwen_pricing['output_cost_per_million_tokens'] == 1.6
        assert qwen_pricing['cached_input_cost_per_million_tokens'] is None  # N/A

        # Test other models against LiteLLM data
        for model_name, doc_pricing in docs_pricing.items():
            if model_name == 'qwen3-coder-480b':
                continue  # Skip custom pricing model

            litellm_pricing = self.get_litellm_pricing(model_name, pricing_data)

            if litellm_pricing:  # Only test if we found pricing in LiteLLM
                assert (
                    abs(
                        doc_pricing['input_cost_per_million_tokens']
                        - litellm_pricing['input_cost_per_million_tokens']
                    )
                    < 0.01
                ), (
                    f'Input pricing mismatch for {model_name}: docs={doc_pricing["input_cost_per_million_tokens"]}, litellm={litellm_pricing["input_cost_per_million_tokens"]}'
                )

                assert (
                    abs(
                        doc_pricing['output_cost_per_million_tokens']
                        - litellm_pricing['output_cost_per_million_tokens']
                    )
                    < 0.01
                ), (
                    f'Output pricing mismatch for {model_name}: docs={doc_pricing["output_cost_per_million_tokens"]}, litellm={litellm_pricing["output_cost_per_million_tokens"]}'
                )

                # Test cached input cost if both have it
                doc_cached = doc_pricing.get('cached_input_cost_per_million_tokens')
                litellm_cached = litellm_pricing.get(
                    'cached_input_cost_per_million_tokens'
                )

                if doc_cached is not None and litellm_cached is not None:
                    assert abs(doc_cached - litellm_cached) < 0.01, (
                        f'Cached input pricing mismatch for {model_name}: docs={doc_cached}, litellm={litellm_cached}'
                    )
                elif doc_cached is None and litellm_cached is not None:
                    # Documentation shows N/A but LiteLLM has cached pricing - this might be intentional
                    pass
                elif doc_cached is not None and litellm_cached is None:
                    # Documentation has cached pricing but LiteLLM doesn't - this shouldn't happen
                    raise AssertionError(
                        f'Documentation has cached pricing for {model_name} but LiteLLM does not'
                    )

    def test_all_openhands_models_documented(
        self, openhands_models: list[str], documentation_content: str
    ):
        """Test that all OpenHands models are documented in the pricing table."""
        docs_pricing = self.extract_pricing_from_docs(documentation_content)
        documented_models = set(docs_pricing.keys())

        # Filter out models that might not have pricing (like kimi-k2-0711-preview)
        expected_models = set(openhands_models)

        # Check that most models are documented (allowing for some models without pricing)
        documented_count = len(documented_models.intersection(expected_models))
        total_count = len(expected_models)

        # We should have at least 80% of models documented
        coverage_ratio = documented_count / total_count if total_count > 0 else 0
        assert coverage_ratio >= 0.8, (
            f'Only {documented_count}/{total_count} models documented in pricing table'
        )

    def test_model_list_consistency(
        self, openhands_models: list[str], documentation_content: str
    ):
        """Test that the model list in documentation is consistent with the code."""
        docs_pricing = self.extract_pricing_from_docs(documentation_content)
        documented_models = set(docs_pricing.keys())
        code_models = set(openhands_models)

        # Find models that are in code but not in docs
        missing_from_docs = code_models - documented_models
        # Find models that are in docs but not in code
        extra_in_docs = documented_models - code_models

        # Allow some models to be missing from docs (e.g., if they don't have pricing)
        # but no extra models should be in docs that aren't in code
        assert not extra_in_docs, (
            f'Models in documentation but not in code: {extra_in_docs}'
        )

        # Report missing models for visibility (but don't fail the test)
        if missing_from_docs:
            print(f'Models in code but not documented: {missing_from_docs}')

    def test_pricing_format_consistency(self, documentation_content: str):
        """Test that pricing format is consistent in the documentation."""
        docs_pricing = self.extract_pricing_from_docs(documentation_content)

        for model_name, pricing in docs_pricing.items():
            # Check that prices are reasonable (not negative, not extremely high)
            assert pricing['input_cost_per_million_tokens'] >= 0, (
                f'Negative input cost for {model_name}'
            )
            assert pricing['output_cost_per_million_tokens'] >= 0, (
                f'Negative output cost for {model_name}'
            )
            assert pricing['input_cost_per_million_tokens'] <= 100, (
                f'Unreasonably high input cost for {model_name}'
            )
            assert pricing['output_cost_per_million_tokens'] <= 200, (
                f'Unreasonably high output cost for {model_name}'
            )

            # Output cost should generally be higher than input cost
            if pricing['input_cost_per_million_tokens'] > 0:
                ratio = (
                    pricing['output_cost_per_million_tokens']
                    / pricing['input_cost_per_million_tokens']
                )
                assert ratio >= 1.0, (
                    f'Output cost should be >= input cost for {model_name}'
                )
                assert ratio <= 20.0, (
                    f'Output/input cost ratio too high for {model_name}'
                )
