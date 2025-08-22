import { useTranslation } from "react-i18next";
import { FaInfoCircle } from "react-icons/fa";
import { ConnectToProviderMessage } from "./connect-to-provider-message";
import { RepositorySelectionForm } from "./repo-selection-form";
import { useConfig } from "#/hooks/query/use-config";
import { RepoProviderLinks } from "./repo-provider-links";
import { useUserProviders } from "#/hooks/use-user-providers";
import { GitRepository } from "#/types/git";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface RepoConnectorProps {
  onRepoSelection: (repo: GitRepository | null) => void;
}

export function RepoConnector({ onRepoSelection }: RepoConnectorProps) {
  const { providers } = useUserProviders();
  const { data: config } = useConfig();
  const { t } = useTranslation();

  const isSaaS = config?.APP_MODE === "saas";
  const providersAreSet = providers.length > 0;

  return (
    <section
      data-testid="repo-connector"
      className="w-full flex flex-col gap-6"
    >
      <div className="flex items-center gap-2">
        <h2 className="heading">{t("HOME$CONNECT_TO_REPOSITORY")}</h2>
        <TooltipButton
          testId="repo-connector-info"
          tooltip={t("HOME$CONNECT_TO_REPOSITORY_TOOLTIP")}
          ariaLabel={t("HOME$CONNECT_TO_REPOSITORY_TOOLTIP")}
          className="text-[#9099AC] hover:text-white"
          placement="bottom"
          tooltipClassName="max-w-[348px]"
        >
          <FaInfoCircle size={16} />
        </TooltipButton>
      </div>

      {!providersAreSet && <ConnectToProviderMessage />}
      {providersAreSet && (
        <RepositorySelectionForm onRepoSelection={onRepoSelection} />
      )}

      {isSaaS && providersAreSet && <RepoProviderLinks />}
    </section>
  );
}
