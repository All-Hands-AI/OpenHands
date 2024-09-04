import GitHubClient from "#/utils/github-client";

const ghClient = new GitHubClient({
  auth: null,
});
export { ghClient };
