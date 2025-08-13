/* eslint-disable i18next/no-literal-string */
import React from "react";
import { useTranslation } from "react-i18next";
import { useSettings } from "#/hooks/query/use-settings";
import { useAddGitProviders } from "#/hooks/mutation/use-add-git-providers";
import { useUserProviders } from "#/hooks/use-user-providers";
import { BrandButton } from "#/components/features/settings/brand-button";
import { GitHubTokenInput } from "#/components/features/settings/git-settings/github-token-input";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";

interface ProviderAuth {
  token: string;
  host: string;
}

interface ProvidersPayload {
  github: ProviderAuth;
  gitlab: ProviderAuth;
  bitbucket: ProviderAuth;
  enterprise_sso: ProviderAuth;
}

export default function ConnectGitHubScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: settings, isLoading } = useSettings();
  const { providers } = useUserProviders();

  const { mutate: saveGitProviders, isPending } = useAddGitProviders();

  const [githubTokenInputHasValue, setGithubTokenInputHasValue] =
    React.useState(false);
  const [githubHostInputHasValue, setGithubHostInputHasValue] =
    React.useState(false);

  const existingGithubHost = settings?.PROVIDER_TOKENS_SET.github;
  const isGitHubTokenSet = providers.includes("github");

  const repoSectionRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    // When providers are set, ensure repository queries are hot and scroll into view
    if (providers.length > 0) {
      queryClient.invalidateQueries({ queryKey: ["repositories"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["installations"], exact: false });
      if (repoSectionRef.current) {
        repoSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [providers.length, queryClient]);

  const onSave = async (formData: FormData) => {
    const githubToken = formData.get("github-token-input")?.toString() || "";
    const githubHost = formData.get("github-host-input")?.toString() || "";

    const providersPayload: ProvidersPayload = {
      github: { token: githubToken, host: githubHost },
      gitlab: { token: "", host: "" },
      bitbucket: { token: "", host: "" },
      enterprise_sso: { token: "", host: "" },
    };

    saveGitProviders(
      { providers: providersPayload },
      {
        onSuccess: () => {
          displaySuccessToast(t("SETTINGS$SAVED"));
          setGithubTokenInputHasValue(false);
          setGithubHostInputHasValue(false);
          // Bring repo list into view right after save
          if (repoSectionRef.current) {
            repoSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        },
        onError: (error) => {
          const errorMessage = retrieveAxiosErrorMessage(error);
          displayErrorToast(errorMessage || t("ERROR$GENERIC"));
        },
      },
    );
  };

  const handleRepoSelection = React.useCallback((repo: any) => {
    if (!repo) return;
    // Navigate to workspace route after selection
    navigate("/workspace", { replace: false });
  }, [navigate]);

  const startGithubOAuth = async () => {
    try {
      const res = await fetch("/api/auth/github/start");
      if (!res.ok) throw new Error("Failed to start GitHub OAuth");
      const data = await res.json();
      if (data?.auth_url) {
        window.location.href = data.auth_url;
      } else {
        displayErrorToast("OAuth URL not received");
      }
    } catch (e) {
      displayErrorToast("Failed to start GitHub OAuth");
    }
  };

  return (
    <div className="flex flex-col gap-6 p-8">
      <h1 className="text-2xl font-semibold text-white">Connect GitHub</h1>

      <form
        action={onSave}
        className="flex flex-col gap-4 p-6 border border-tertiary rounded-lg"
      >
        <GitHubTokenInput
          name="github-token-input"
          isGitHubTokenSet={isGitHubTokenSet}
          onChange={(value) => setGithubTokenInputHasValue(!!value)}
          onGitHubHostChange={(value) => setGithubHostInputHasValue(!!value)}
          githubHostSet={existingGithubHost}
        />

        <div className="flex gap-3 justify-between">
          <BrandButton
            variant="secondary"
            type="button"
            onClick={startGithubOAuth}
          >
            Connect with GitHub (OAuth)
          </BrandButton>

          <BrandButton
            testId="connect-github-save"
            type="submit"
            variant="primary"
            isDisabled={
              isPending ||
              (!githubTokenInputHasValue && !githubHostInputHasValue)
            }
          >
            {!isPending && t("SETTINGS$SAVE_CHANGES")}
            {isPending && t("SETTINGS$SAVING")}
          </BrandButton>
        </div>
      </form>

      <section ref={repoSectionRef} className="mt-2">
        <h2 className="text-xl font-medium text-white mb-3">
          Select Repository
        </h2>
        {!isLoading && <RepoConnector onRepoSelection={handleRepoSelection} />}
      </section>
    </div>
  );
}
