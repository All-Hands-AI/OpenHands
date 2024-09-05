import {
  ActionFunctionArgs,
  json,
  LoaderFunctionArgs,
  redirect,
} from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { SuggestionBox } from "./suggestion-box";
import { TaskForm } from "./task-form";
import { HeroHeading } from "./hero-heading";
import { GitHubRepositorySelector } from "./github-repo-selector";
import { getSession } from "#/sessions";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"));
  const ghToken = session.get("ghToken");

  let repos: GitHubRepository[] = [];
  if (ghToken) {
    const data = await retrieveGitHubUserRepositories(ghToken);
    if (!isGitHubErrorReponse(data)) repos = data;
    // TODO: display error message in the UI
    else console.warn(data.status, data.message);
  }

  return json({ repos });
};

export const action = async ({ request }: ActionFunctionArgs) => {
  const formData = await request.formData();
  const q = formData.get("q")?.toString();

  if (q) {
    const searchParams = new URLSearchParams({ q });
    return redirect(`/app?${searchParams}`);
  }

  return json(null);
};

function Home() {
  const { repos } = useLoaderData<typeof loader>();

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
          content={<GitHubRepositorySelector repositories={repos} />}
        />
        <SuggestionBox title="+ Import Project" content="from your desktop" />
      </div>
    </div>
  );
}

export default Home;
