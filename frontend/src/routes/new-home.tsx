import { TaskSuggestions } from "#/components/features/home/task-suggestions";
import { BrandButton } from "#/components/features/settings/brand-button";

function RepoConnector() {
  return (
    <section className="flex-1">
      <h2 className="heading">Connect to a Repository</h2>
      <select aria-label="Select a Repo">
        <option>Select a Repo</option>
      </select>
      <button type="button">Launch</button>
      <div>
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitHub repositories
        </a>
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitLab repositories
        </a>
      </div>
    </section>
  );
}

function HomeHeader() {
  return (
    <header className="flex justify-between items-end">
      <section className="flex flex-col gap-5">
        <div
          aria-label="all hands ai logo"
          className="w-[100px] h-[70px] bg-gray-50"
        />
        <h1 className="heading">Let&apos;s Start Building!</h1>
        <p className="text-sm max-w-[424px]">
          OpenHands makes it easy to build and maintain software using AI-driven
          development.
        </p>
      </section>

      <section className="flex flex-col gap-4">
        <BrandButton variant="primary" type="button" className="w-full">
          Launch from Scratch
        </BrandButton>
        <p className="text-sm">
          Not sure how to start?{" "}
          <a
            href="http://"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2"
          >
            Read this
          </a>
        </p>
      </section>
    </header>
  );
}

function HomeScreen() {
  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full rounded-xl p-[42px]"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex justify-between">
        <RepoConnector />
        <TaskSuggestions />
      </main>
    </div>
  );
}

export default HomeScreen;
