import React from "react";
import { PrefetchPageLinks } from "react-router";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useUserProviders } from "#/hooks/use-user-providers";
import { GitRepository } from "#/types/git";
import { NewConversation } from "#/components/features/home/new-conversation";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { providers } = useUserProviders();
  const [selectedRepo, setSelectedRepo] = React.useState<GitRepository | null>(
    null,
  );

  const providersAreSet = providers.length > 0;

  return (
    <div
      data-testid="home-screen"
      className="bg-[#26282D] h-full flex flex-col pt-[35px] overflow-y-auto"
    >
      <HomeHeader />

      <div className="pt-[25px] flex justify-center">
        <div className="flex flex-col gap-5 px-6 sm:max-w-full sm:min-w-full md:flex-row lg:px-0 lg:max-w-[703px] lg:min-w-[703px]">
          <RepoConnector onRepoSelection={(repo) => setSelectedRepo(repo)} />
          <NewConversation />
        </div>
      </div>

      <div className="pt-[12px] flex justify-center mb-[262px]">
        <div className="flex flex-col gap-5 px-6 md:flex-row md:max-w-full md:min-w-full lg:px-0 lg:max-w-[703px] lg:min-w-[703px]">
          {providersAreSet && <TaskSuggestions filterFor={selectedRepo} />}
        </div>
      </div>
    </div>
  );
}

export default HomeScreen;
