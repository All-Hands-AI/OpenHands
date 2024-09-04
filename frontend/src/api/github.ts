import GitHubClient from "#/utils/github-client";

const ghClient = new GitHubClient({
  auth: localStorage.getItem("GITHUB_TOKEN"),
});
export { ghClient };
