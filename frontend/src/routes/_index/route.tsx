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
import { convertImageToBase64 } from "#/utils/convert-image-to-base-64";
import store from "#/store";
import { addFile, setInitialQuery } from "#/state/initial-query-slice";

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
  const isFileUpload = !!request.headers
    .get("Content-Type")
    ?.includes("multipart");

  if (isFileUpload) {
    const formData = await request.formData();
    const file = formData.get("file");
    if (file instanceof File) {
      // TODO: Take care of this if SSR is enabled (store is not available on the server)
      store.dispatch(addFile(await convertImageToBase64(file)));
    }
    return json({ success: true });
  }

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

  return (
    <div className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center gap-16 relative">
      {navigation.state === "loading" && (
        <div className="absolute top-8 right-8">
          <LoadingSpinner size="small" />
        </div>
      )}
      <HeroHeading />
      <div className="flex flex-col gap-16 items-center">
        <TaskForm />
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
          <SuggestionBox title="+ Import Project" content="from your desktop" />
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
