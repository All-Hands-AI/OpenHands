import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";

function HomeScreen() {
  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl p-[42px] gap-8"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex justify-between overflow-y-auto">
        <RepoConnector />
        <TaskSuggestions />
      </main>
    </div>
  );
}

export default HomeScreen;
