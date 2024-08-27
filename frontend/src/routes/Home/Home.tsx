import React from "react";
import {
  ActionFunctionArgs,
  json,
  redirect,
  useFetcher,
} from "react-router-dom";
import { SuggestionBox } from "./SuggestionBox";
import { TaskForm } from "./TaskForm";
import { HeroHeading } from "./HeroHeading";
import { parseGithubUrl } from "#/utils/parseGithubUrl";

const fetchRepositoryData = async (
  owner: string,
  repository: string,
): Promise<{ id: string }> => {
  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repository}`,
  );

  return response.json();
};

export const action = async ({ request }: ActionFunctionArgs) => {
  const formData = await request.formData();
  const intent = formData.get("intent");

  if (intent?.toString() === "repo") {
    const repoUrl = formData.get("repo");
    if (repoUrl?.toString()) {
      const [owner, repository] = parseGithubUrl(repoUrl.toString());
      const data = await fetchRepositoryData(owner, repository);

      return json(data);
    }

    return json(null);
  }

  if (intent?.toString() === "task") {
    const q = formData.get("q");

    if (q?.toString()) {
      return redirect(`/app?q=${q.toString()}`);
    }

    return json(null);
  }

  return json(null);
};

function Home() {
  const fetcher = useFetcher();

  return (
    <div className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center gap-16">
      <HeroHeading />
      <TaskForm />
      <div className="flex gap-4">
        <SuggestionBox
          title="Make a To-do List App"
          description="Track your daily work"
        />
        <SuggestionBox
          title="Clone Repo"
          description="Create your token here"
        />
        <div className="w-[304px] h-[100px] border border-[#525252] rounded-xl flex flex-col items-center justify-center gap-1 px-4">
          <span className="text-[16px] leading-6 -tracking-[0.01em] font-[600]">
            Open a Repo
          </span>
          <fetcher.Form method="post" className="relative w-full">
            <input
              name="repo"
              type="text"
              className="text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]"
              placeholder="https://github.com/{owner}/{repo}"
            />
            <button
              name="intent"
              value="repo"
              type="submit"
              hidden
              aria-hidden
            />
          </fetcher.Form>
        </div>
        <SuggestionBox
          title="+ Import Project"
          description="from your desktop"
        />
      </div>
    </div>
  );
}

export default Home;
