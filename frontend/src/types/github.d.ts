interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

interface GitHubUser {
  id: number;
  login: string;
  avatar_url: string;
  company: string | null;
  name: string | null;
  email: string | null;
}

interface GitHubRepository {
  id: number;
  full_name: string;
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
