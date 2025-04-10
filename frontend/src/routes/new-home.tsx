import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import React from "react";

function HomeScreen() {
  const [selectedRepoTitle, setSelectedRepoTitle] = React.useState<
    string | null
  >(null);

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl p-[42px] gap-8"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex justify-between overflow-y-auto">
        <RepoConnector
          onRepoSelection={(title) => setSelectedRepoTitle(title)}
        />
        <TaskSuggestions filterFor={selectedRepoTitle} />
      </main>
    </div>
  );
}

export default HomeScreen;
