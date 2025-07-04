import { Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function AzureDevOpsTokenHelpAnchor() {
  return (
    <p data-testid="azure-devops-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.AZURE_DEVOPS$TOKEN_HELP_TEXT}
        components={[
          <a
            key="azure-devops-token-help-anchor-link"
            aria-label="Azure DevOps token help link"
            href="https://dev.azure.com/_usersSettings/tokens"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="azure-devops-token-help-anchor-link-2"
            aria-label="Azure DevOps token see more link"
            href="https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
