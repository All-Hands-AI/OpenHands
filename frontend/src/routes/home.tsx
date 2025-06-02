import React from "react";
import { PrefetchPageLinks } from "react-router";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { ReplaySuggestionBox } from "#/components/features/suggestions/replay-suggestion-box";
import { useUserProviders } from "#/hooks/use-user-providers";
import { ENABLE_TRAJECTORY_REPLAY } from "#/utils/feature-flags";
import { setReplayJson } from "#/state/initial-query-slice";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { providers } = useUserProviders();
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [selectedRepoTitle, setSelectedRepoTitle] = React.useState<
    string | null
  >(null);

  const providersAreSet = providers.length > 0;

  const handleReplayFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        const fileContent = await file.text();
        // Attempt to parse to ensure it's valid JSON, though we store the string
        JSON.parse(fileContent);
        dispatch(setReplayJson(fileContent));
        displaySuccessToast(t(I18nKey.EXPLORER$UPLOAD_SUCCESS_MESSAGE));
        posthog.capture("trajectory_replay_uploaded_on_home", {
          file_name: file.name,
          file_size: file.size,
        });
      } catch (error) {
        dispatch(setReplayJson(null));
        displayErrorToast(t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE));
      } finally {
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    }
  };

  return (
    <div
      data-testid="home-screen"
      className="bg-base-secondary h-full flex flex-col rounded-xl px-[42px] pt-[42px] gap-8 overflow-y-auto"
    >
      <HomeHeader />

      <hr className="border-[#717888]" />

      <main className="flex flex-col md:flex-row justify-between gap-8">
        <div className="flex flex-col gap-8 flex-1">
          <RepoConnector
            onRepoSelection={(title) => setSelectedRepoTitle(title)}
          />
          {ENABLE_TRAJECTORY_REPLAY() && (
            <ReplaySuggestionBox
              onChange={handleReplayFileChange}
              fileInputRef={fileInputRef}
            />
          )}
        </div>
        <hr className="md:hidden border-[#717888]" />
        {providersAreSet && <TaskSuggestions filterFor={selectedRepoTitle} />}
      </main>
    </div>
  );
}

export default HomeScreen;
