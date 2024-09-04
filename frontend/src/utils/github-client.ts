class GitHubClient {
  private url = "https://api.github.com";

  private headers: HeadersInit = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${this.config.auth}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };

  constructor(private config: { auth: string | null }) {}

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

  /**
   * https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repositories-for-the-authenticated-user
   * @returns The repositories of the authenticated user
   */
  public async getRepositories(): Promise<GitHubRepository[]> {
    const response = await fetch(`${this.url}/user/repos`, {
      headers: this.headers,
    });
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    return response.json();
  }
}

export default GitHubClient;
