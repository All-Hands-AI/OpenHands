


"""Features mixin for AWS CodeCommit service."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from openhands.core.logger import openhands_logger as logger


class CodeCommitFeaturesMixin:
    """Features mixin for AWS CodeCommit service."""

    async def get_file_content(
        self, repository: str, path: str, ref: str | None = None
    ) -> dict[str, Any]:
        """Get file content.

        Args:
            repository: Repository name
            path: File path
            ref: Git reference (branch, tag, commit)

        Returns:
            File content
        """
        try:
            # Get file content
            if ref:
                response = self.client.get_file(
                    repositoryName=repository,
                    filePath=path,
                    commitSpecifier=ref
                )
            else:
                # Use default branch if ref is not specified
                repo_info = self.client.get_repository(
                    repositoryName=repository
                )['repositoryMetadata']
                
                default_branch = repo_info.get('defaultBranch', 'main')
                
                response = self.client.get_file(
                    repositoryName=repository,
                    filePath=path,
                    commitSpecifier=default_branch
                )
            
            # Return file content
            return {
                'content': response['fileContent'],
                'encoding': 'base64',
                'size': response['fileSize'],
                'name': path.split('/')[-1],
                'path': path,
                'sha': response['blobId'],
            }
            
        except ClientError as e:
            logger.error(f"Failed to get file content for {path} in repository {repository}: {e}")
            raise

    async def get_directory_content(
        self, repository: str, path: str, ref: str | None = None
    ) -> list[dict[str, Any]]:
        """Get directory content.

        Args:
            repository: Repository name
            path: Directory path
            ref: Git reference (branch, tag, commit)

        Returns:
            Directory content
        """
        try:
            # Normalize path
            if path.startswith('/'):
                path = path[1:]
            if path and not path.endswith('/'):
                path = path + '/'
                
            # Get directory content
            if ref:
                response = self.client.get_folder(
                    repositoryName=repository,
                    folderPath=path if path != '/' else '',
                    commitSpecifier=ref
                )
            else:
                # Use default branch if ref is not specified
                repo_info = self.client.get_repository(
                    repositoryName=repository
                )['repositoryMetadata']
                
                default_branch = repo_info.get('defaultBranch', 'main')
                
                response = self.client.get_folder(
                    repositoryName=repository,
                    folderPath=path if path != '/' else '',
                    commitSpecifier=default_branch
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
                
            return content
            
        except ClientError as e:
            logger.error(f"Failed to get directory content for {path} in repository {repository}: {e}")
            raise

    async def get_commit(self, repository: str, ref: str) -> dict[str, Any]:
        """Get commit information.

        Args:
            repository: Repository name
            ref: Git reference (commit SHA)

        Returns:
            Commit information
        """
        try:
            # Get commit information
            response = self.client.get_commit(
                repositoryName=repository,
                commitId=ref
            )
            
            commit_info = response['commit']
            
            # Return commit information
            return {
                'sha': commit_info['commitId'],
                'author': {
                    'name': commit_info.get('author', {}).get('name', ''),
                    'email': commit_info.get('author', {}).get('email', ''),
                    'date': commit_info.get('author', {}).get('date', '').isoformat() if commit_info.get('author', {}).get('date') else None,
                },
                'committer': {
                    'name': commit_info.get('committer', {}).get('name', ''),
                    'email': commit_info.get('committer', {}).get('email', ''),
                    'date': commit_info.get('committer', {}).get('date', '').isoformat() if commit_info.get('committer', {}).get('date') else None,
                },
                'message': commit_info.get('message', ''),
                'parents': [parent['commitId'] for parent in commit_info.get('parents', [])],
            }
            
        except ClientError as e:
            logger.error(f"Failed to get commit information for {ref} in repository {repository}: {e}")
            raise

    async def get_commits(
        self, repository: str, path: str | None = None, ref: str | None = None
    ) -> list[dict[str, Any]]:
        """Get commits for a repository or file.

        Args:
            repository: Repository name
            path: File path
            ref: Git reference (branch, tag, commit)

        Returns:
            List of commits
        """
        try:
            # Determine the commit specifier
            commit_specifier = ref
            if not commit_specifier:
                # Use default branch if ref is not specified
                repo_info = self.client.get_repository(
                    repositoryName=repository
                )['repositoryMetadata']
                
                commit_specifier = repo_info.get('defaultBranch', 'main')
            
            # Get commits
            if path:
                # Get commits for a specific file
                response = self.client.get_commits(
                    repositoryName=repository,
                    path=path,
                    commitSpecifier=commit_specifier
                )
            else:
                # Get commits for the repository
                response = self.client.get_commits(
                    repositoryName=repository,
                    commitSpecifier=commit_specifier
                )
            
            # Process commits
            commits = []
            for commit_id in response.get('commits', []):
                try:
                    # Get detailed commit information
                    commit_info = self.client.get_commit(
                        repositoryName=repository,
                        commitId=commit_id
                    )['commit']
                    
                    # Add commit to the list
                    commits.append({
                        'sha': commit_info['commitId'],
                        'author': {
                            'name': commit_info.get('author', {}).get('name', ''),
                            'email': commit_info.get('author', {}).get('email', ''),
                            'date': commit_info.get('author', {}).get('date', '').isoformat() if commit_info.get('author', {}).get('date') else None,
                        },
                        'committer': {
                            'name': commit_info.get('committer', {}).get('name', ''),
                            'email': commit_info.get('committer', {}).get('email', ''),
                            'date': commit_info.get('committer', {}).get('date', '').isoformat() if commit_info.get('committer', {}).get('date') else None,
                        },
                        'message': commit_info.get('message', ''),
                        'parents': [parent['commitId'] for parent in commit_info.get('parents', [])],
                    })
                except ClientError as e:
                    logger.error(f"Failed to get detailed commit information for {commit_id}: {e}")
                    continue
                    
            return commits
            
        except ClientError as e:
            logger.error(f"Failed to get commits for repository {repository}: {e}")
            raise

    async def get_diff(
        self, repository: str, base: str, head: str, path: str | None = None
    ) -> str:
        """Get diff between two commits.

        Args:
            repository: Repository name
            base: Base commit
            head: Head commit
            path: File path

        Returns:
            Diff
        """
        try:
            # Get differences between commits
            if path:
                # Get diff for a specific file
                response = self.client.get_differences(
                    repositoryName=repository,
                    beforeCommitSpecifier=base,
                    afterCommitSpecifier=head,
                    path=path
                )
            else:
                # Get diff for the entire repository
                response = self.client.get_differences(
                    repositoryName=repository,
                    beforeCommitSpecifier=base,
                    afterCommitSpecifier=head
                )
            
            # Format the diff
            diff_output = []
            for diff in response.get('differences', []):
                if 'beforeBlob' in diff and 'afterBlob' in diff:
                    # File was modified
                    diff_output.append(f"diff --git a/{diff['beforeBlob']['path']} b/{diff['afterBlob']['path']}")
                    diff_output.append(f"index {diff['beforeBlob']['blobId'][:7]}..{diff['afterBlob']['blobId'][:7]} 100644")
                    diff_output.append(f"--- a/{diff['beforeBlob']['path']}")
                    diff_output.append(f"+++ b/{diff['afterBlob']['path']}")
                    
                    # Get the actual content diff
                    try:
                        before_content = self.client.get_blob(
                            repositoryName=repository,
                            blobId=diff['beforeBlob']['blobId']
                        )['content'].decode('utf-8')
                        
                        after_content = self.client.get_blob(
                            repositoryName=repository,
                            blobId=diff['afterBlob']['blobId']
                        )['content'].decode('utf-8')
                        
                        # Simple line-by-line diff (simplified)
                        before_lines = before_content.splitlines()
                        after_lines = after_content.splitlines()
                        
                        # Add a simple hunk header
                        diff_output.append(f"@@ -1,{len(before_lines)} +1,{len(after_lines)} @@")
                        
                        # Add removed lines
                        for line in before_lines:
                            diff_output.append(f"-{line}")
                            
                        # Add added lines
                        for line in after_lines:
                            diff_output.append(f"+{line}")
                            
                    except Exception as e:
                        logger.error(f"Failed to get blob content: {e}")
                        diff_output.append("Binary files differ")
                        
                elif 'beforeBlob' in diff and 'afterBlob' not in diff:
                    # File was deleted
                    diff_output.append(f"diff --git a/{diff['beforeBlob']['path']} b/{diff['beforeBlob']['path']}")
                    diff_output.append(f"deleted file mode 100644")
                    diff_output.append(f"index {diff['beforeBlob']['blobId'][:7]}..0000000")
                    diff_output.append(f"--- a/{diff['beforeBlob']['path']}")
                    diff_output.append(f"+++ /dev/null")
                    
                elif 'beforeBlob' not in diff and 'afterBlob' in diff:
                    # File was added
                    diff_output.append(f"diff --git a/{diff['afterBlob']['path']} b/{diff['afterBlob']['path']}")
                    diff_output.append(f"new file mode 100644")
                    diff_output.append(f"index 0000000..{diff['afterBlob']['blobId'][:7]}")
                    diff_output.append(f"--- /dev/null")
                    diff_output.append(f"+++ b/{diff['afterBlob']['path']}")
                    
            return '\n'.join(diff_output)
            
        except ClientError as e:
            logger.error(f"Failed to get diff between {base} and {head} for repository {repository}: {e}")
            raise


