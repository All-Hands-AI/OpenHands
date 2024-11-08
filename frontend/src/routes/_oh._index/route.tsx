import {
  Await,
  ClientActionFunctionArgs,
  ClientLoaderFunctionArgs,
  defer,
  redirect,
  useLoaderData,
  useNavigate,
  useRouteLoaderData,
} from "@remix-run/react";
import React from "react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { SuggestionBox } from "./suggestion-box";
import { TaskForm } from "./task-form";
import { HeroHeading } from "./hero-heading";
import { retrieveAllGitHubUserRepositories } from "#/api/github";
import store from "#/store";
import {
  setImportedProjectZip,
  setInitialQuery,
} from "#/state/initial-query-slice";
import { clientLoader as rootClientLoader } from "#/routes/_oh";
import OpenHands from "#/api/open-hands";
import { generateGitHubAuthUrl } from "#/utils/generate-github-auth-url";
import { GitHubRepositoriesSuggestionBox } from "#/components/github-repositories-suggestion-box";
import { convertZipToBase64 } from "#/utils/convert-zip-to-base64";

export const clientLoader = async ({ request }: ClientLoaderFunctionArgs) => {
  let isSaas = false;
  let githubClientId: string | null = null;

  try {
    const config = await OpenHands.getConfig();
    isSaas = config.APP_MODE === "saas";
    githubClientId = config.GITHUB_CLIENT_ID;
  } catch (error) {
    isSaas = false;
    githubClientId = null;
  }

  const ghToken = localStorage.getItem("ghToken");
  const token = localStorage.getItem("token");
  if (token) return redirect("/app");

  let repositories: ReturnType<
    typeof retrieveAllGitHubUserRepositories
  > | null = null;
  if (ghToken) {
    const data = retrieveAllGitHubUserRepositories(ghToken);
    repositories = data;
  }

  let githubAuthUrl: string | null = null;
  if (isSaas && githubClientId) {
    const requestUrl = new URL(request.url);
    githubAuthUrl = generateGitHubAuthUrl(githubClientId, requestUrl);
  }

  return defer({ repositories, githubAuthUrl });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const q = formData.get("q")?.toString();
  if (q) store.dispatch(setInitialQuery(q));

  posthog.capture("initial_query_submitted", {
    query_character_length: q?.length,
  });

  return redirect("/app");
};

function Home() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const rootData = useRouteLoaderData<typeof rootClientLoader>("routes/_oh");
  const { repositories, githubAuthUrl } = useLoaderData<typeof clientLoader>();

  return (
    <div
      data-testid="root-index"
      className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto"
    >
      <HeroHeading />
      <div className="flex flex-col gap-16 w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          <TaskForm />
        </div>
        <div className="flex gap-4 w-full">
          <React.Suspense
            fallback={
              <SuggestionBox
                title="Open a Repo"
                content="Loading repositories..."
              />
            }
          >
            <Await resolve={repositories}>
              {(resolvedRepositories) => (
                <GitHubRepositoriesSuggestionBox
                  repositories={resolvedRepositories}
                  gitHubAuthUrl={githubAuthUrl}
                  user={rootData?.user || null}
                />
              )}
            </Await>
          </React.Suspense>
          <SuggestionBox
            title="+ Import Project"
            content={
              <label
                htmlFor="import-project"
                className="w-full flex justify-center"
              >
                <span className="border-2 border-dashed border-neutral-600 rounded px-2 py-1 cursor-pointer">
                  Upload a .zip
                </span>
                <input
                  hidden
                  type="file"
                  accept="application/zip"
                  id="import-project"
                  multiple={false}
                  onChange={async (event) => {
                    if (event.target.files) {
                      const zip = event.target.files[0];
                      dispatch(
                        setImportedProjectZip(await convertZipToBase64(zip)),
                      );
                      navigate("/app");
                    } else {
                      // TODO: handle error
                    }
                  }}
                />
              </label>
            }
          />
        </div>
      </div>
    </div>
  );
}

export default Home;
