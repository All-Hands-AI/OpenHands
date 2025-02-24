import asyncio
import os
from pydantic import SecretStr

from openhands.integrations.github.github_service import GitHubService

async def main():
    token = SecretStr(os.environ.get('GITHUB_TOKEN', ''))
    service = GitHubService(token=token)
    
    print("Getting user info...")
    user = await service.get_user()
    print(f"Authenticated as: {user.login}")
    
    print("\nFetching recent repositories...")
    repos = await service.get_repositories(page=1, per_page=10, sort="pushed", installation_id=None)
    print(f"Found {len(repos)} repositories:")
    for repo in repos:
        print(f"- {repo.full_name}")
    
    print("\nFetching suggested tasks...")
    tasks = await service.get_suggested_tasks()
    
    print("\nFound tasks:")
    if not tasks:
        print("No tasks found")
    for task in tasks:
        print(f"\n{task.task_type} in {task.repo}:")
        print(f"#{task.issue_number}: {task.title}")

if __name__ == "__main__":
    asyncio.run(main())