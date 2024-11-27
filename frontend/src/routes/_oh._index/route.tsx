import { useLocation, useNavigate } from "@remix-run/react";
import React from "react";
import { useDispatch } from "react-redux";
import { TaskForm } from "./task-form";
import { HeroHeading } from "./hero-heading";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import { GitHubRepositoriesSuggestionBox } from "#/components/github-repositories-suggestion-box";
import { convertZipToBase64 } from "#/utils/convert-zip-to-base64";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";
import { useAuth } from "#/context/auth-context";
import { ImportProjectSuggestionBox } from "./import-project-suggestion-box";

function Home() {
  const { token, gitHubToken } = useAuth();

  const dispatch = useDispatch();
  const location = useLocation();
  const navigate = useNavigate();

  const formRef = React.useRef<HTMLFormElement>(null);

  const { data: config } = useConfig();
  const { data: user } = useGitHubUser();
  const { data: repositories } = useUserRepositories();

  const gitHubAuthUrl = useGitHubAuthUrl({
    gitHubToken,
    appMode: config?.APP_MODE || null,
    gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  });

  React.useEffect(() => {
    if (token) navigate("/app");
  }, [location.pathname]);

  return (
    <div
      data-testid="root-index"
      className="bg-root-secondary h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto"
    >
      <HeroHeading />
      <div className="flex flex-col gap-16 w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          <TaskForm ref={formRef} />
        </div>

        <div className="flex gap-4 w-full">
          <GitHubRepositoriesSuggestionBox
            handleSubmit={() => formRef.current?.requestSubmit()}
            repositories={
              repositories?.pages.flatMap((page) => page.data) || []
            }
            gitHubAuthUrl={gitHubAuthUrl}
            user={user || null}
          />
          <ImportProjectSuggestionBox
            onChange={async (event) => {
              if (event.target.files) {
                const zip = event.target.files[0];
                dispatch(setImportedProjectZip(await convertZipToBase64(zip)));
                formRef.current?.requestSubmit();
              } else {
                // TODO: handle error
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default Home;
