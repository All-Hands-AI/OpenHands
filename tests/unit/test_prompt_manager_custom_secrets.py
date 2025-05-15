import os

import pytest

from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


@pytest.fixture
def prompt_dir(tmp_path):
    # Create a temporary directory for prompt templates
    return tmp_path


def test_build_workspace_context_with_custom_secrets_descriptions(prompt_dir):
    """Test that build_workspace_context includes custom_secrets_descriptions in the template."""
    # Create an additional_info.j2 template file that includes custom_secrets_descriptions
    with open(os.path.join(prompt_dir, 'additional_info.j2'), 'w') as f:
        f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
Repository: {{ repository_info.repo_name }}
</REPOSITORY_INFO>
{% endif %}

{% if runtime_info and runtime_info.custom_secrets_descriptions %}
<RUNTIME_SECRETS>
The following custom secrets are available:
{% for secret_name, secret_description in runtime_info.custom_secrets_descriptions.items() %}
* {{ secret_name }}: {{ secret_description }}
{% endfor %}
</RUNTIME_SECRETS>
{% endif %}
""")

    # Create microagent_info.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'microagent_info.j2'), 'w') as f:
        f.write('{% for agent in triggered_agents %}{{ agent.content }}{% endfor %}')

    # Create system_prompt.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write('System prompt')

    # Create user_prompt.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt')

    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Create repository and runtime information with custom_secrets_descriptions
    repo_info = RepositoryInfo(repo_name='owner/repo', repo_directory='/workspace/repo')
    runtime_info = RuntimeInfo(
        date='2025-05-15',
        custom_secrets_descriptions={
            'API_KEY': 'Your API key for service X',
            'DB_PASSWORD': 'Database password',
        },
    )

    # Build workspace context
    result = manager.build_workspace_context(
        repository_info=repo_info, runtime_info=runtime_info, repo_instructions=''
    )

    # Check that custom_secrets_descriptions are included in the output
    assert '<RUNTIME_SECRETS>' in result
    assert 'The following custom secrets are available:' in result
    assert '* API_KEY: Your API key for service X' in result
    assert '* DB_PASSWORD: Database password' in result
    assert '</RUNTIME_SECRETS>' in result


def test_build_workspace_context_with_empty_custom_secrets_descriptions(prompt_dir):
    """Test that build_workspace_context handles empty custom_secrets_descriptions correctly."""
    # Create an additional_info.j2 template file that includes custom_secrets_descriptions
    with open(os.path.join(prompt_dir, 'additional_info.j2'), 'w') as f:
        f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
Repository: {{ repository_info.repo_name }}
</REPOSITORY_INFO>
{% endif %}

{% if runtime_info and runtime_info.custom_secrets_descriptions %}
<RUNTIME_SECRETS>
The following custom secrets are available:
{% for secret_name, secret_description in runtime_info.custom_secrets_descriptions.items() %}
* {{ secret_name }}: {{ secret_description }}
{% endfor %}
</RUNTIME_SECRETS>
{% endif %}
""")

    # Create microagent_info.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'microagent_info.j2'), 'w') as f:
        f.write('{% for agent in triggered_agents %}{{ agent.content }}{% endfor %}')

    # Create system_prompt.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'system_prompt.j2'), 'w') as f:
        f.write('System prompt')

    # Create user_prompt.j2 template (required by PromptManager)
    with open(os.path.join(prompt_dir, 'user_prompt.j2'), 'w') as f:
        f.write('User prompt')

    # Initialize the PromptManager
    manager = PromptManager(prompt_dir=prompt_dir)

    # Create repository and runtime information with empty custom_secrets_descriptions
    repo_info = RepositoryInfo(repo_name='owner/repo', repo_directory='/workspace/repo')
    runtime_info = RuntimeInfo(date='2025-05-15', custom_secrets_descriptions={})

    # Build workspace context
    result = manager.build_workspace_context(
        repository_info=repo_info, runtime_info=runtime_info, repo_instructions=''
    )

    # Check that the RUNTIME_SECRETS section is not included when custom_secrets_descriptions is empty
    assert '<RUNTIME_SECRETS>' not in result
    assert 'The following custom secrets are available:' not in result
