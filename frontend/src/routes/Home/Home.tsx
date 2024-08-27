import React from "react";
import { ActionFunctionArgs, json, redirect } from "react-router-dom";
import { SuggestionBox } from "./SuggestionBox";
import { TaskForm } from "./TaskForm";
import { HeroHeading } from "./HeroHeading";

export const action = async ({ request }: ActionFunctionArgs) => {
  const formData = await request.formData();
  const q = formData.get("q");

  if (q?.toString()) {
    return redirect(`/app?q=${q.toString()}`);
  }

  return json(null);
};

function Home() {
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
          title="Connect to GitHub"
          description="Create your token here"
        />
        <SuggestionBox
          title="+ Import Project"
          description="from your desktop"
        />
      </div>
    </div>
  );
}

export default Home;
