import {
  ClientActionFunctionArgs,
  json,
  redirect,
  useLoaderData,
  useNavigation,
} from "@remix-run/react";
import React from "react";
import { SuggestionBox } from "./suggestion-box";
import { TaskForm } from "./task-form";
import { HeroHeading } from "./hero-heading";
import { GitHubRepositorySelector } from "./github-repo-selector";
import {
  isGitHubErrorReponse,
  retrieveAllGitHubUserRepositories,
} from "#/api/github";
import ModalButton from "#/components/buttons/ModalButton";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import { ConnectToGitHubModal } from "#/components/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { LoadingSpinner } from "#/components/modals/LoadingProject";
import store from "#/store";
import { setInitialQuery } from "#/state/initial-query-slice";

export const clientLoader = async () => {
  const ghToken = localStorage.getItem("ghToken");
  const token = localStorage.getItem("token");

  if (token) {
    return redirect("/app");
  }

  let repositories: GitHubRepository[] = [];
  if (ghToken) {
    const data = await retrieveAllGitHubUserRepositories(ghToken);
    if (!isGitHubErrorReponse(data)) {
      repositories = data;
    }
  }

  return json({ repositories, ghToken });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const q = formData.get("q")?.toString();
  if (q) store.dispatch(setInitialQuery(q));

  return redirect("/app");
};

function Home() {
  const navigation = useNavigation();
  const { repositories, ghToken } = useLoaderData<typeof clientLoader>();
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);
  const [importedFile, setImportedFile] = React.useState<File | null>(null);

  return (
    <div className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center relative">
      {navigation.state === "loading" && (
        <div className="absolute top-8 right-8">
          <LoadingSpinner size="small" />
        </div>
      )}
      <HeroHeading />
      <div className="flex flex-col gap-16 items-center">
        <TaskForm importedProjectZip={importedFile} />
        <div className="flex gap-4 w-full">
          <SuggestionBox
            title="Open a Repo"
            content={
              ghToken ? (
                <GitHubRepositorySelector repositories={repositories} />
              ) : (
                <ModalButton
                  text="Connect to GitHub"
                  icon={<GitHubLogo width={20} height={20} />}
                  className="bg-[#791B80] w-full"
                  onClick={() => setConnectToGitHubModalOpen(true)}
                />
              )
            }
          />
          <SuggestionBox
            title={importedFile ? "Project Loaded" : "+ Import Project"}
            content={
              importedFile?.name ?? (
                <label
                  htmlFor="import-project"
                  className="w-full flex justify-center"
                >
                  <span className="border-2 border-dashed border-neutral-600 rounded px-2 py-1 cursor-pointer">
                    Click here to load
                  </span>
                  <input
                    hidden
                    type="file"
                    accept="application/zip"
                    id="import-project"
                    multiple={false}
                    onChange={(event) => {
                      if (event.target.files) {
                        const zip = event.target.files[0];
                        setImportedFile(zip);
                      } else {
                        // TODO: handle error
                      }
                    }}
                  />
                </label>
              )
            }
          />
        </div>
      </div>
      {connectToGitHubModalOpen && (
        <ModalBackdrop>
          <ConnectToGitHubModal
            onClose={() => setConnectToGitHubModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </div>
  );
}

export default Home;
