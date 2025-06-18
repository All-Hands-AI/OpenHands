import { Provider } from "#/types/settings";

interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

interface GitUser {
  id: string;
  login: string;
  avatar_url: string;
  company: string | null;
  name: string | null;
  email: string | null;
}

interface Branch {
  name: string;
  commit_sha: string;
  protected: boolean;
  last_push_date?: string;
}

interface GitRepository {
  id: string;
  full_name: string;
  git_provider: Provider;
  is_public: boolean;
  stargazers_count?: number;
  link_header?: string;
  pushed_at?: string;
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
