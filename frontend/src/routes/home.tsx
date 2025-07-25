import React from "react";
import { PrefetchPageLinks } from "react-router";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useUserProviders } from "#/hooks/use-user-providers";
import { GitRepository } from "#/types/git";
import { NewProject } from "#/components/features/home/new-project";
import { RecentProjects } from "#/components/features/home/recent-projects";
import { useResizeWindow } from "#/hooks/use-resize-window";
import { cn } from "#/utils/utils";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { providers } = useUserProviders();
  const [selectedRepo, setSelectedRepo] = React.useState<GitRepository | null>(
    null,
  );

  const { isSmallerDevice } = useResizeWindow();

  const providersAreSet = providers.length > 0;

  return (
    <div
      data-testid="home-screen"
      className="bg-[#2F3137] h-full flex flex-col pt-[47px] overflow-y-auto"
    >
      <HomeHeader />

      <div className="pt-[70px] flex justify-center">
        <div
          className={cn(
            "flex gap-[20px] md:max-w-full md:min-w-full lg:max-w-[703px] lg:min-w-[703px]",
            isSmallerDevice && "flex-col max-w-full min-w-full",
          )}
        >
          <RepoConnector onRepoSelection={(repo) => setSelectedRepo(repo)} />
          <NewProject />
        </div>
      </div>

      <div className="pt-[12px] flex justify-center mb-[262px]">
        <div
          className={cn(
            "flex gap-[20px] md:max-w-full md:min-w-full lg:max-w-[703px] lg:min-w-[703px]",
            isSmallerDevice && "flex-col max-w-full min-w-full",
          )}
        >
          <RecentProjects />
          {providersAreSet && <TaskSuggestions filterFor={selectedRepo} />}
        </div>
      </div>
    </div>
  );
}

export default HomeScreen;
