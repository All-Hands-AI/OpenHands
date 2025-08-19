from openhands.integrations.github.service._base import GitHubMixinBase
from openhands.integrations.service_types import RequestMethod


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
