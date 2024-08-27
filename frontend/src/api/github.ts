import GitHubClient from "#/utils/github-client";

const ghClient = new GitHubClient({ auth: import.meta.env.VITE_GITHUB_TOKEN });
export { ghClient };
