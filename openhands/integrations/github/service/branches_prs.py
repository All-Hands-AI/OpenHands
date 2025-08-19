from openhands.integrations.github.service._base import GitHubMixinBase
from openhands.integrations.service_types import Branch, RequestMethod


class GitHubBranchesMixin(GitHubMixinBase):
    async def get_branches(self, repository: str) -> list[Branch]:
        url = f'{self.BASE_URL}/repos/{repository}/branches'
        MAX_BRANCHES = 5000
        PER_PAGE = 100

        all_branches: list[Branch] = []
        page = 1

        while len(all_branches) < MAX_BRANCHES:
            params = {'per_page': str(PER_PAGE), 'page': str(page)}
            response, headers = await self._make_request(url, params)

            if not response:
                break

            for branch_data in response:
                last_push_date = None
                if branch_data.get('commit') and branch_data['commit'].get('commit'):
                    commit_info = branch_data['commit']['commit']
                    if commit_info.get('committer') and commit_info['committer'].get(
                        'date'
                    ):
                        last_push_date = commit_info['committer']['date']

                branch = Branch(
                    name=branch_data.get('name'),
                    commit_sha=branch_data.get('commit', {}).get('sha', ''),
                    protected=branch_data.get('protected', False),
                    last_push_date=last_push_date,
                )
                all_branches.append(branch)

            page += 1

            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        return all_branches


class GitHubPRsMixin(GitHubMixinBase):
    async def create_pr(
        self,
        repo_name: str,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str | None = None,
        draft: bool = True,
        labels: list[str] | None = None,
    ) -> str:
        url = f'{self.BASE_URL}/repos/{repo_name}/pulls'

        if not body:
            body = f'Merging changes from {source_branch} into {target_branch}'

        payload = {
            'title': title,
            'head': source_branch,
            'base': target_branch,
            'body': body,
            'draft': draft,
        }

        response, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        if labels and len(labels) > 0:
            pr_number = response['number']
            labels_url = f'{self.BASE_URL}/repos/{repo_name}/issues/{pr_number}/labels'
            labels_payload = {'labels': labels}
            await self._make_request(
                url=labels_url, params=labels_payload, method=RequestMethod.POST
            )

        return response['html_url']
