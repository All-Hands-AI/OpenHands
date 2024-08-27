import React from "react";
import {
  ActionFunctionArgs,
  json,
  redirect,
  useLoaderData,
} from "react-router-dom";
import { SuggestionBox } from "./SuggestionBox";
import { TaskForm } from "./TaskForm";
import { HeroHeading } from "./HeroHeading";
import { ghClient } from "#/api/github";
import { GitHubRepositorySelector } from "./GitHubRepositorySelector";

type LoaderReturnType = {
  repos: GitHubRepository[];
};

export const loader = async () => {
  const repos = await ghClient.getRepositories();
  return json({ repos });
};

export const action = async ({ request }: ActionFunctionArgs) => {
  const formData = await request.formData();
  const q = formData.get("q");

  if (q?.toString()) {
    return redirect(`/app?q=${q.toString()}`);
  }

  return json(null);
};

function Home() {
  const { repos } = useLoaderData() as LoaderReturnType;

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
