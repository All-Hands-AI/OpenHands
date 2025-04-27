from openhands.integrations.service_types import ProviderType, SuggestedTask, TaskType

def get_provider_terms(git_provider: ProviderType) -> dict:
    if git_provider == ProviderType.GITLAB:
        return {
            "requestType": "Merge Request",
            "requestTypeShort": "MR",
            "apiName": "GitLab API",
            "tokenEnvVar": "GITLAB_TOKEN",
            "ciSystem": "CI pipelines",
            "ciProvider": "GitLab",
            "requestVerb": "merge request",
        }
    elif git_provider == ProviderType.GITHUB:
        return {
            "requestType": "Pull Request",
            "requestTypeShort": "PR",
            "apiName": "GitHub API",
            "tokenEnvVar": "GITHUB_TOKEN",
            "ciSystem": "GitHub Actions",
            "ciProvider": "GitHub",
            "requestVerb": "pull request",
        }

    raise ValueError(f"Provider {git_provider} for suggested task prompts")

def get_merge_conflict_prompt(git_provider: ProviderType, issue_number: int, repo: str) -> str:
    terms = get_provider_terms(git_provider)
    return (
        f"You are working on {terms['requestType']} #{issue_number} in repository {repo}. You need to fix the merge conflicts.\n"
        f"Use the {terms['apiName']} with the {terms['tokenEnvVar']} environment variable to retrieve the {terms['requestTypeShort']} details. "
        f"Check out the branch from that {terms['requestVerb']} and look at the diff versus the base branch of the {terms['requestTypeShort']} to understand the {terms['requestTypeShort']}'s intention.\n"
        "Then resolve the merge conflicts. If you aren't sure what the right solution is, look back through the commit history at the commits that introduced the conflict and resolve them accordingly."
    )

def get_failing_checks_prompt(git_provider: ProviderType, issue_number: int, repo: str) -> str:
    terms = get_provider_terms(git_provider)
    return (
        f"You are working on {terms['requestType']} #{issue_number} in repository {repo}. You need to fix the failing CI checks.\n"
        f"Use the {terms['apiName']} with the {terms['tokenEnvVar']} environment variable to retrieve the {terms['requestTypeShort']} details. "
        f"Check out the branch from that {terms['requestVerb']} and look at the diff versus the base branch of the {terms['requestTypeShort']} to understand the {terms['requestTypeShort']}'s intention.\n"
        f"Then use the {terms['apiName']} to look at the {terms['ciSystem']} that are failing on the most recent commit. Try and reproduce the failure locally.\n"
        "Get things working locally, then push your changes. Sleep for 30 seconds at a time until the "
        f"{terms['ciProvider']} {terms['ciSystem'].lower()} have run again. If they are still failing, repeat the process."
    )

def get_unresolved_comments_prompt(git_provider: ProviderType, issue_number: int, repo: str) -> str:
    terms = get_provider_terms(git_provider)
    return (
        f"You are working on {terms['requestType']} #{issue_number} in repository {repo}. You need to resolve the remaining comments from reviewers.\n"
        f"Use the {terms['apiName']} with the {terms['tokenEnvVar']} environment variable to retrieve the {terms['requestTypeShort']} details. "
        f"Check out the branch from that {terms['requestVerb']} and look at the diff versus the base branch of the {terms['requestTypeShort']} to understand the {terms['requestTypeShort']}'s intention.\n"
        f"Then use the {terms['apiName']} to retrieve all the feedback on the {terms['requestTypeShort']} so far. "
        "If anything hasn't been addressed, address it and commit your changes back to the same branch."
    )

def get_open_issue_prompt(git_provider: ProviderType, issue_number: int, repo: str) -> str:
    terms = get_provider_terms(git_provider)
    return (
        f"You are working on Issue #{issue_number} in repository {repo}. Your goal is to fix the issue.\n"
        f"Use the {terms['apiName']} with the {terms['tokenEnvVar']} environment variable to retrieve the issue details and any comments on the issue. "
        "Then check out a new branch and investigate what changes will need to be made.\n"
        f"Finally, make the required changes and open up a {terms['requestVerb']}. Be sure to reference the issue in the {terms['requestTypeShort']} description."
    )

def get_prompt_for_task(
    task: SuggestedTask
) -> str:
    task_type = task.task_type
    git_provider = task.git_provider
    issue_number = task.issue_number
    repo = task.repo

    if task_type == TaskType.MERGE_CONFLICTS:
        return get_merge_conflict_prompt(git_provider, issue_number, repo)
    elif task_type == TaskType.FAILING_CHECKS:
        return get_failing_checks_prompt(git_provider, issue_number, repo)
    elif task_type == TaskType.UNRESOLVED_COMMENTS:
        return get_unresolved_comments_prompt(git_provider, issue_number, repo)
    elif task_type == TaskType.OPEN_ISSUE:
        return get_open_issue_prompt(git_provider, issue_number, repo)
    else:
        return ""
