import React from "react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setReplayJson } from "#/state/initial-query-slice";
import { useGitUser } from "#/hooks/query/use-git-user";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";
import { ReplaySuggestionBox } from "#/components/features/suggestions/replay-suggestion-box";
import { GitRepositoriesSuggestionBox } from "#/components/features/git/git-repositories-suggestion-box";
import { CodeNotInGitLink } from "#/components/features/git/code-not-in-github-link";
import { HeroHeading } from "#/components/shared/hero-heading";
import { TaskForm } from "#/components/shared/task-form";
import { convertFileToText } from "#/utils/convert-file-to-text";
import { ENABLE_TRAJECTORY_REPLAY } from "#/utils/feature-flags";

function Home() {
  const dispatch = useDispatch();
  const formRef = React.useRef<HTMLFormElement>(null);

  const { data: config } = useConfig();
  const { data: user } = useGitUser();

  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config?.APP_MODE || null,
    gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  });

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto px-2"
    >
      <HeroHeading />
      <div className="flex flex-col gap-1 w-full mt-8 md:w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          <TaskForm ref={formRef} />
        </div>

        <div className="flex gap-4 w-full flex-col md:flex-row mt-8">
          <GitRepositoriesSuggestionBox
            handleSubmit={() => formRef.current?.requestSubmit()}
            gitHubAuthUrl={gitHubAuthUrl}
            user={user || null}
          />
          {ENABLE_TRAJECTORY_REPLAY() && (
            <ReplaySuggestionBox
              onChange={async (event) => {
                if (event.target.files) {
                  const json = event.target.files[0];
                  dispatch(setReplayJson(await convertFileToText(json)));
                  posthog.capture("json_file_uploaded");
                  formRef.current?.requestSubmit();
                } else {
                  // TODO: handle error
                }
              }}
            />
          )}
        </div>
        <div className="w-full flex justify-start mt-2 ml-2">
          <CodeNotInGitLink />
        </div>
      </div>
    </div>
  );
}

export default Home;
