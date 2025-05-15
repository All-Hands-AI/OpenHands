import React from "react";
import { PrefetchPageLinks } from "react-router";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useUserConnected } from "#/hooks/query/use-user-connected";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { data: isUserConnected } = useUserConnected();
  const [selectedRepoTitle, setSelectedRepoTitle] = React.useState<
    string | null
  >(null);

  const providersAreSet = isUserConnected === true;

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex flex-col md:flex-row justify-between gap-8">
        <RepoConnector
          onRepoSelection={(title) => setSelectedRepoTitle(title)}
        />
        <hr className="md:hidden border-[#717888]" />
        {providersAreSet && <TaskSuggestions filterFor={selectedRepoTitle} />}
      </main>
    </div>
  );
}

export default HomeScreen;
