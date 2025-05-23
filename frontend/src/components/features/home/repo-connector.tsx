import { useTranslation } from "react-i18next";
import { ConnectToProviderMessage } from "./connect-to-provider-message";
import { RepositorySelectionForm } from "./repo-selection-form";
import { useConfig } from "#/hooks/query/use-config";
import { RepoProviderLinks } from "./repo-provider-links";
import { useUserConnected } from "#/hooks/query/use-user-connected";

interface RepoConnectorProps {
  onRepoSelection: (repoTitle: string | null) => void;
}

export function RepoConnector({ onRepoSelection }: RepoConnectorProps) {
  const { data: isUserConnected, isLoading } = useUserConnected();
  const { data: config } = useConfig();
  const { t } = useTranslation();

  const isSaaS = config?.APP_MODE === "saas";
  const providersAreSet = isUserConnected === true;

  return (
    <section
      data-testid="repo-connector"
      className="w-full flex flex-col gap-6"
    >
      <h2 className="heading">{t("HOME$CONNECT_TO_REPOSITORY")}</h2>

      {!isLoading && !providersAreSet && <ConnectToProviderMessage />}
      {!isLoading && providersAreSet && (
        <RepositorySelectionForm onRepoSelection={onRepoSelection} />
      )}

      {isSaaS && providersAreSet && <RepoProviderLinks />}
    </section>
  );
}
