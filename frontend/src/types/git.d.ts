import { Provider } from "#/types/settings";

interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

interface GitUser {
  id: number;
  login: string;
  avatar_url: string;
  company: string | null;
  name: string | null;
  email: string | null;
}

interface GitRepository {
  id: number;
  full_name: string;
  git_provider: Provider;
  stargazers_count?: number;
  link_header?: string;
}

interface GitHubCommit {
  html_url: string;
  sha: string;
  commit: {
    author: {
      date: string; // ISO 8601
    };
  };
}

interface GithubAppInstallation {
  installations: { id: number }[];
}
