import requests


class GitHubService:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def get_user(self):
        response = requests.get('https://api.github.com/user', headers=self.headers)
        response.raise_for_status()

        return response.json()
