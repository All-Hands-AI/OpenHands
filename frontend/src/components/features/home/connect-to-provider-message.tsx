import { Link } from "react-router";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useSettings } from "#/hooks/query/use-settings";

export function ConnectToProviderMessage() {
  const { isLoading } = useSettings();

  return (
    <div className="flex flex-col gap-4">
      <p>
        To get started with suggested tasks, please connect your GitHub or
        GitLab account.
      </p>
      <Link data-testid="navigate-to-settings-button" to="/settings">
        <BrandButton type="button" variant="primary" isDisabled={isLoading}>
          {!isLoading && "Go to Settings"}
          {isLoading && "Loading..."}
        </BrandButton>
      </Link>
    </div>
  );
}
