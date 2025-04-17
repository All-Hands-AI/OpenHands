import React from "react";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useAuth } from "#/context/auth-context";

function HomeScreen() {
  const { providersAreSet } = useAuth();
  const [selectedRepoTitle, setSelectedRepoTitle] = React.useState<
    string | null
  >(null);

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex justify-between overflow-y-auto">
        <RepoConnector
          onRepoSelection={(title) => setSelectedRepoTitle(title)}
        />
        {providersAreSet && <TaskSuggestions filterFor={selectedRepoTitle} />}
      </main>
    </div>
  );
}

export default HomeScreen;
