#!/usr/bin/env python3
import re

# Files to update
files = [
    'tests/unit/resolver/github/test_send_pull_request.py',
    'tests/unit/resolver/gitlab/test_gitlab_pr_title_escaping.py',
    'tests/unit/resolver/gitlab/test_gitlab_send_pull_request.py',
]

for file_path in files:
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace function name
    content = content.replace(
        'def test_send_pull_request_legacy(', 'def test_send_pull_request('
    )

    # Replace patch decorators
    content = content.replace(
        "@patch('openhands.resolver.send_pull_request.send_pull_request_legacy')",
        "@patch('openhands.resolver.send_pull_request.send_pull_request')",
    )

    # Replace function calls
    pattern = r'send_pull_request_legacy\(\s*issue=([^,]+),\s*token=([^,]+),\s*username=([^,]+),\s*platform=([^,]+),\s*patch_dir=([^,]+),\s*pr_type=([^,]+)'

    def replacement(match):
        issue = match.group(1).strip()
        token = match.group(2).strip()
        username = match.group(3).strip()
        platform = match.group(4).strip()
        patch_dir = match.group(5).strip()
        pr_type = match.group(6).strip()

        provider = 'github' if 'GITHUB' in platform else 'gitlab'

        return f"""send_pull_request(
        provider='{provider}',
        owner={issue}.owner,
        repo={issue}.repo,
        title=f'Fix issue #{{{issue}.number}}: {{{issue}.title}}',
        body=ANY,
        head='',
        base='',
        token={token},
        username={username},
        patch_dir={patch_dir},
        pr_type={pr_type}"""

    content = re.sub(pattern, replacement, content)

    with open(file_path, 'w') as f:
        f.write(content)

print('Files updated successfully!')
