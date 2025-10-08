


"""Resolver mixin for AWS CodeCommit service."""

from __future__ import annotations

import re
from typing import Any

from botocore.exceptions import ClientError

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import Repository


class CodeCommitResolverMixin:
    """Resolver mixin for AWS CodeCommit service."""

    async def resolve_repository_from_url(self, url: str) -> Repository:
        """Resolve repository from URL.

        Args:
            url: Repository URL

        Returns:
            Repository
        """
        try:
            # Extract repository name from URL
            # CodeCommit URLs can be in the format:
            # https://git-codecommit.{region}.amazonaws.com/v1/repos/{repository}
            # or
            # https://{region}.console.aws.amazon.com/codecommit/home?region={region}#/repository/{repository}
            
            repo_name = None
            
            # Try to match the git URL pattern
            git_url_match = re.search(r'git-codecommit\.[^.]+\.amazonaws\.com/v1/repos/([^/]+)', url)
            if git_url_match:
                repo_name = git_url_match.group(1)
                
            # Try to match the console URL pattern
            console_url_match = re.search(r'console\.aws\.amazon\.com/codecommit/home.*#/repository/([^/]+)', url)
            if console_url_match:
                repo_name = console_url_match.group(1)
                
            if not repo_name:
                raise ValueError(f"Could not extract repository name from URL: {url}")
                
            # Get repository details
            repo_info = self.client.get_repository(
                repositoryName=repo_name
            )['repositoryMetadata']
            
            # Create Repository object
            return Repository(
                id=repo_info['repositoryId'],
                name=repo_info['repositoryName'],
                full_name=repo_info['repositoryName'],
                description=repo_info.get('repositoryDescription', ''),
                url=f"https://git-codecommit.{self.region}.amazonaws.com/v1/repos/{repo_info['repositoryName']}",
                private=True,  # CodeCommit repositories are always private
                owner=repo_info.get('accountId', ''),
                provider='codecommit',
                default_branch=repo_info.get('defaultBranch', 'main'),
                created_at=repo_info.get('creationDate', '').isoformat() if repo_info.get('creationDate') else None,
                updated_at=repo_info.get('lastModifiedDate', '').isoformat() if repo_info.get('lastModifiedDate') else None,
            )
            
        except ClientError as e:
            logger.error(f"Failed to resolve repository from URL {url}: {e}")
            raise

    async def resolve_pull_request_from_url(self, url: str) -> dict[str, Any]:
        """Resolve pull request from URL.

        Args:
            url: Pull request URL

        Returns:
            Pull request information
        """
        try:
            # Extract repository name and pull request ID from URL
            # CodeCommit URLs can be in the format:
            # https://{region}.console.aws.amazon.com/codecommit/home?region={region}#/repository/{repository}/pull-request/{pr_id}
            
            url_match = re.search(r'console\.aws\.amazon\.com/codecommit/home.*#/repository/([^/]+)/pull-request/([^/]+)', url)
            if not url_match:
                raise ValueError(f"Could not extract repository name and pull request ID from URL: {url}")
                
            repo_name = url_match.group(1)
            pr_id = url_match.group(2)
            
            # Get pull request details
            pr_info = self.client.get_pull_request(
                pullRequestId=pr_id
            )['pullRequest']
            
            # Return pull request information
            return {
                'repository': repo_name,
                'pull_number': pr_id,
                'title': pr_info['title'],
                'body': pr_info.get('description', ''),
                'state': pr_info['pullRequestStatus'].lower(),
                'head': pr_info['pullRequestTargets'][0]['sourceReference'],
                'base': pr_info['pullRequestTargets'][0]['destinationReference'],
            }
            
        except ClientError as e:
            logger.error(f"Failed to resolve pull request from URL {url}: {e}")
            raise

    async def resolve_issue_from_url(self, url: str) -> dict[str, Any]:
        """Resolve issue from URL.

        Args:
            url: Issue URL

        Returns:
            Issue information
        """
        # CodeCommit doesn't have separate issues, only pull requests
        # Redirect to resolve_pull_request_from_url
        return await self.resolve_pull_request_from_url(url)

    async def resolve_file_from_url(self, url: str) -> dict[str, Any]:
        """Resolve file from URL.

        Args:
            url: File URL

        Returns:
            File information
        """
        try:
            # Extract repository name, branch/commit, and file path from URL
            # CodeCommit URLs can be in the format:
            # https://{region}.console.aws.amazon.com/codecommit/home?region={region}#/repository/{repository}/browse/{branch}/--/{path}
            
            url_match = re.search(r'console\.aws\.amazon\.com/codecommit/home.*#/repository/([^/]+)/browse/([^/]+)/--/(.*)', url)
            if not url_match:
                raise ValueError(f"Could not extract repository name, branch/commit, and file path from URL: {url}")
                
            repo_name = url_match.group(1)
            ref = url_match.group(2)
            path = url_match.group(3)
            
            # Get file content
            response = self.client.get_file(
                repositoryName=repo_name,
                filePath=path,
                commitSpecifier=ref
            )
            
            # Return file information
            return {
                'repository': repo_name,
                'path': path,
                'ref': ref,
                'content': response['fileContent'],
                'encoding': 'base64',
                'size': response['fileSize'],
                'name': path.split('/')[-1],
                'sha': response['blobId'],
            }
            
        except ClientError as e:
            logger.error(f"Failed to resolve file from URL {url}: {e}")
            raise

    async def resolve_directory_from_url(self, url: str) -> dict[str, Any]:
        """Resolve directory from URL.

        Args:
            url: Directory URL

        Returns:
            Directory information
        """
        try:
            # Extract repository name, branch/commit, and directory path from URL
            # CodeCommit URLs can be in the format:
            # https://{region}.console.aws.amazon.com/codecommit/home?region={region}#/repository/{repository}/browse/{branch}/--/{path}
            
            url_match = re.search(r'console\.aws\.amazon\.com/codecommit/home.*#/repository/([^/]+)/browse/([^/]+)/--/(.*)', url)
            if not url_match:
                raise ValueError(f"Could not extract repository name, branch/commit, and directory path from URL: {url}")
                
            repo_name = url_match.group(1)
            ref = url_match.group(2)
            path = url_match.group(3)
            
            # Normalize path
            if path.startswith('/'):
                path = path[1:]
            if path and not path.endswith('/'):
                path = path + '/'
                
            # Get directory content
            response = self.client.get_folder(
                repositoryName=repo_name,
                folderPath=path if path != '/' else '',
                commitSpecifier=ref
            )
            
            # Process files and subfolders
            content = []
            
            # Add files
            for file_info in response.get('files', []):
                content.append({
                    'name': file_info['relativePath'].split('/')[-1],
                    'path': file_info['relativePath'],
                    'type': 'file',
                    'size': file_info['size'],
                    'sha': file_info['blobId'],
                })
                
            # Add subfolders
            for subfolder in response.get('subFolders', []):
                content.append({
                    'name': subfolder['relativePath'].split('/')[-1],
                    'path': subfolder['relativePath'],
                    'type': 'dir',
                })
                
            # Add symbolic links
            for symlink in response.get('symbolicLinks', []):
                content.append({
                    'name': symlink['relativePath'].split('/')[-1],
                    'path': symlink['relativePath'],
                    'type': 'symlink',
                })
                
            # Return directory information
            return {
                'repository': repo_name,
                'path': path,
                'ref': ref,
                'content': content,
            }
            
        except ClientError as e:
            logger.error(f"Failed to resolve directory from URL {url}: {e}")
            raise


