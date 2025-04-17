import { ConnectToProviderMessage } from "./connect-to-provider-message";
import { useAuth } from "#/context/auth-context";
import { RepositorySelectionForm } from "./repo-selection-form";

interface RepoConnectorProps {
  onRepoSelection: (repoTitle: string | null) => void;
}

export function RepoConnector({ onRepoSelection }: RepoConnectorProps) {
  const { providersAreSet } = useAuth();

  return (
    <section
      data-testid="repo-connector"
      className="w-full flex flex-col gap-6"
    >
      <h2 className="heading">Connect to a Repository</h2>

      {!providersAreSet && <ConnectToProviderMessage />}
      {providersAreSet && (
        <RepositorySelectionForm onRepoSelection={onRepoSelection} />
      )}
    </section>
  );
}
