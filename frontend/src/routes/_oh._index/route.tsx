import React from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import { I18nKey } from "#/i18n/declaration";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import { convertZipToBase64 } from "#/utils/convert-zip-to-base64";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";
import { ImportProjectSuggestionBox } from "../../components/features/suggestions/import-project-suggestion-box";
import { GitHubRepositoriesSuggestionBox } from "#/components/features/github/github-repositories-suggestion-box";
import { HeroHeading } from "#/components/shared/hero-heading";
import { TaskForm } from "#/components/shared/task-form";

function Home() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const formRef = React.useRef<HTMLFormElement>(null);

  const { data: config } = useConfig();
  const { data: user } = useGitHubUser();

  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config?.APP_MODE || null,
    gitHubClientId: config?.GITHUB_CLIENT_ID || null,
  });

  const latestConversation = localStorage.getItem("latest_conversation_id");

  return (
    <div className="bg-base-secondary h-full rounded-xl flex flex-col items-center justify-center relative overflow-y-auto px-2">
      <HeroHeading />
      <div className="flex flex-col gap-8 w-full md:w-[600px] items-center">
        <div className="flex flex-col gap-2 w-full">
          <TaskForm ref={formRef} />
        </div>

        <div className="flex gap-4 w-full flex-col md:flex-row">
          <GitHubRepositoriesSuggestionBox
            handleSubmit={() => formRef.current?.requestSubmit()}
            gitHubAuthUrl={gitHubAuthUrl}
            user={user || null}
          />
          <ImportProjectSuggestionBox
            onChange={async (event) => {
              if (event.target.files) {
                const zip = event.target.files[0];
                dispatch(setImportedProjectZip(await convertZipToBase64(zip)));
                posthog.capture("zip_file_uploaded");
                formRef.current?.requestSubmit();
              } else {
                // TODO: handle error
              }
            }}
          />
        </div>
      </div>
      {latestConversation && (
        <div className="flex gap-4 w-full text-center mt-8">
          <p className="text-center w-full">
            {t(I18nKey.LANDING$OR)}&nbsp;
            <a
              className="underline"
              href={`/conversations/${latestConversation}`}
            >
              {t(I18nKey.LANDING$RECENT_CONVERSATION)}
            </a>
          </p>
        </div>
      )}
    </div>
  );
}

export default Home;
