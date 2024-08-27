class GitHubClient {
  private url = "https://api.github.com";

  private headers: HeadersInit = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${this.config.auth}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };

  constructor(private config: { auth: string }) {}

  /**
   * https://docs.github.com/en/rest/users/users?apiVersion=2022-11-28#get-the-authenticated-user
   * @returns The authenticated user
   */
  public async getUser(): Promise<GitHubUser> {
    const response = await fetch(`${this.url}/user`, {
      headers: this.headers,
    });
    return response.json();
  }
}

export default GitHubClient;
