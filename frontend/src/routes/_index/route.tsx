import {
  ClientActionFunctionArgs,
  json,
  redirect,
  useLoaderData,
} from "@remix-run/react";
import { SuggestionBox } from "./suggestion-box";
import { TaskForm } from "./task-form";
import { HeroHeading } from "./hero-heading";
import { GitHubRepositorySelector } from "./github-repo-selector";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";

export const clientLoader = async () => {
  const ghToken = localStorage.getItem("ghToken");

  if (ghToken) {
    const data = await retrieveGitHubUserRepositories(ghToken);
    if (!isGitHubErrorReponse(data)) {
      return json({ repositories: data });
    }
  }

  return json({ repositories: [] });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const searchParams = new URLSearchParams();

  const url = new URL(request.url);
  const repo = url.searchParams.get("repo");

  const formData = await request.formData();
  const q = formData.get("q")?.toString();

  const reset = formData.get("reset")?.toString() === "true";

  if (q) searchParams.set("q", q);
  if (repo) searchParams.set("repo", repo);
  if (reset) {
    searchParams.set("reset", "true");
    localStorage.removeItem("token");
  }

  return redirect(`/app?${searchParams.toString()}`);
};

function Home() {
  const { repositories } = useLoaderData<typeof clientLoader>();

  return (
    <div className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center gap-16">
      <HeroHeading />
      <TaskForm />
      <div className="flex gap-4">
        <SuggestionBox
          title="Make a To-do List App"
          content="Track your daily work"
        />
        <SuggestionBox
          title="Clone Repo"
          content={<GitHubRepositorySelector repositories={repositories} />}
        />
        <SuggestionBox title="+ Import Project" content="from your desktop" />
      </div>
    </div>
  );
}

export default Home;
