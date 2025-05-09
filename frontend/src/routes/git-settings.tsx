import React from "react";
import { useTranslation } from "react-i18next";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useLogout } from "#/hooks/mutation/use-logout";
import { GitHubTokenInput } from "#/components/features/settings/git-settings/github-token-input";
import { GitLabTokenInput } from "#/components/features/settings/git-settings/gitlab-token-input";
import { ConfigureGitHubRepositoriesAnchor } from "#/components/features/settings/git-settings/configure-github-repositories-anchor";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { GitSettingInputsSkeleton } from "#/components/features/settings/git-settings/github-settings-inputs-skeleton";
import { useAddGitProviders } from "#/hooks/mutation/use-add-git-providers";
import { useUserProviders } from "#/hooks/use-user-providers";

function GitSettingsScreen() {
  const { t } = useTranslation();

  const { mutate: saveGitProviders, isPending } = useAddGitProviders();
  const { mutate: disconnectGitTokens } = useLogout();

  const { data: settings, isLoading } = useSettings();
  const { providers } = useUserProviders();

  const { data: config } = useConfig();

  const [githubTokenInputHasValue, setGithubTokenInputHasValue] =
    React.useState(false);
  const [gitlabTokenInputHasValue, setGitlabTokenInputHasValue] =
    React.useState(false);

  const [githubHostInputHasValue, setGithubHostInputHasValue] =
    React.useState(false);
  const [gitlabHostInputHasValue, setGitlabHostInputHasValue] =
    React.useState(false);

  const existingGithubHost = settings?.PROVIDER_TOKENS_SET.github;
  const existingGitlabHost = settings?.PROVIDER_TOKENS_SET.gitlab;

  const isSaas = config?.APP_MODE === "saas";
  const isGitHubTokenSet = providers.includes("github");
  const isGitLabTokenSet = providers.includes("gitlab");

  const formAction = async (formData: FormData) => {
    const disconnectButtonClicked =
      formData.get("disconnect-tokens-button") !== null;

    if (disconnectButtonClicked) {
      disconnectGitTokens();
      return;
    }

    const githubToken = formData.get("github-token-input")?.toString() || "";
    const gitlabToken = formData.get("gitlab-token-input")?.toString() || "";
    const githubHost = formData.get("github-host-input")?.toString() || "";
    const gitlabHost = formData.get("gitlab-host-input")?.toString() || "";

    saveGitProviders(
      {
        providers: {
          github: { token: githubToken, host: githubHost },
          gitlab: { token: gitlabToken, host: gitlabHost },
        },
      },
      {
        onSuccess: () => {
          displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
        },
        onError: (error) => {
          const errorMessage = retrieveAxiosErrorMessage(error);
          displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
        },
        onSettled: () => {
          setGithubTokenInputHasValue(false);
          setGitlabTokenInputHasValue(false);
          setGithubHostInputHasValue(false);
          setGitlabHostInputHasValue(false);
        },
      },
    );
  };

  const formIsClean =
    !githubTokenInputHasValue &&
    !gitlabTokenInputHasValue &&
    !githubHostInputHasValue &&
    !gitlabHostInputHasValue;
  const shouldRenderExternalConfigureButtons = isSaas && config.APP_SLUG;

  return (
    <form
      data-testid="git-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      {!isLoading && (
        <div className="p-9 flex flex-col gap-12">
          {shouldRenderExternalConfigureButtons && !isLoading && (
            <ConfigureGitHubRepositoriesAnchor slug={config.APP_SLUG!} />
          )}

          {!isSaas && (
            <GitHubTokenInput
              name="github-token-input"
              isGitHubTokenSet={isGitHubTokenSet}
              onChange={(value) => {
                setGithubTokenInputHasValue(!!value);
              }}
              onGitHubHostChange={(value) => {
                setGitlabHostInputHasValue(!!value);
              }}
              githubHostSet={existingGithubHost}
            />
          )}

          {!isSaas && (
            <GitLabTokenInput
              name="gitlab-token-input"
              isGitLabTokenSet={isGitLabTokenSet}
              onChange={(value) => {
                setGitlabTokenInputHasValue(!!value);
              }}
              onGitLabHostChange={(value) => {
                setGitlabHostInputHasValue(!!value);
              }}
              gitlabHostSet={existingGitlabHost}
            />
          )}
        </div>
      )}

      {isLoading && <GitSettingInputsSkeleton />}

      <div className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        {!shouldRenderExternalConfigureButtons && (
          <>
            <BrandButton
              testId="disconnect-tokens-button"
              name="disconnect-tokens-button"
              type="submit"
              variant="secondary"
              isDisabled={!isGitHubTokenSet && !isGitLabTokenSet}
            >
              Disconnect Tokens
            </BrandButton>
            <BrandButton
              testId="submit-button"
              type="submit"
              variant="primary"
              isDisabled={isPending || formIsClean}
            >
              {!isPending && t("SETTINGS$SAVE_CHANGES")}
              {isPending && t("SETTINGS$SAVING")}
            </BrandButton>
          </>
        )}
      </div>
    </form>
  );
}

export default GitSettingsScreen;
