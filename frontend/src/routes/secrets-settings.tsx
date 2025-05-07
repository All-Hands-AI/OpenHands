import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Link } from "react-router";
import { useGetSecrets } from "#/hooks/query/use-get-secrets";
import { useDeleteSecret } from "#/hooks/mutation/use-delete-secret";
import { SecretForm } from "#/components/features/settings/secrets-settings/secret-form";
import { SecretListItem } from "#/components/features/settings/secrets-settings/secret-list-item";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ConfirmationModal } from "#/components/shared/modals/confirmation-modal";
import { GetSecretsResponse } from "#/api/secrets-service.types";
import { useUserProviders } from "#/hooks/use-user-providers";

function SecretsSettingsScreen() {
  const queryClient = useQueryClient();

  const { data: secrets } = useGetSecrets();
  const { mutate: deleteSecret } = useDeleteSecret();
  const { providers } = useUserProviders();

  const hasProviderSet = providers.length > 0;

  const [view, setView] = React.useState<
    "list" | "add-secret-form" | "edit-secret-form"
  >("list");
  const [selectedSecret, setSelectedSecret] = React.useState<string | null>(
    null,
  );
  const [confirmationModalIsVisible, setConfirmationModalIsVisible] =
    React.useState(false);

  const deleteSecretOptimistically = (secret: string) => {
    queryClient.setQueryData<GetSecretsResponse["custom_secrets"]>(
      ["secrets"],
      (oldSecrets) => {
        if (!oldSecrets) return [];
        return oldSecrets.filter((s) => s.name !== secret);
      },
    );
  };

  const revertOptimisticUpdate = () => {
    queryClient.invalidateQueries({ queryKey: ["secrets"] });
  };

  const handleDeleteSecret = (secret: string) => {
    deleteSecretOptimistically(secret);
    deleteSecret(secret, {
      onSettled: () => {
        setConfirmationModalIsVisible(false);
      },
      onError: revertOptimisticUpdate,
    });
  };

  const onConfirmDeleteSecret = () => {
    if (selectedSecret) handleDeleteSecret(selectedSecret);
  };

  const onCancelDeleteSecret = () => {
    setConfirmationModalIsVisible(false);
  };

  return (
    <div
      data-testid="secrets-settings-screen"
      className="px-11 py-9 flex flex-col gap-5"
    >
      {!hasProviderSet && (
        <Link to="/settings/git" data-testid="connect-git-button" type="button">
          Connect a Git provider to manage secrets
        </Link>
      )}

      {secrets?.length === 0 && view === "list" && (
        <p data-testid="no-secrets-message">No secrets found</p>
      )}

      {view === "list" && (
        <ul>
          {secrets?.map((secret) => (
            <SecretListItem
              key={secret.name}
              title={secret.name}
              onEdit={() => {
                setView("edit-secret-form");
                setSelectedSecret(secret.name);
              }}
              onDelete={() => {
                setConfirmationModalIsVisible(true);
                setSelectedSecret(secret.name);
              }}
            />
          ))}
        </ul>
      )}

      {hasProviderSet && view === "list" && (
        <BrandButton
          testId="add-secret-button"
          type="button"
          variant="primary"
          onClick={() => setView("add-secret-form")}
        >
          Add a new secret
        </BrandButton>
      )}

      {(view === "add-secret-form" || view === "edit-secret-form") && (
        <SecretForm
          mode={view === "add-secret-form" ? "add" : "edit"}
          selectedSecret={selectedSecret}
          onCancel={() => setView("list")}
        />
      )}

      {confirmationModalIsVisible && (
        <ConfirmationModal
          text="Are you sure you want to delete this key?"
          onConfirm={onConfirmDeleteSecret}
          onCancel={onCancelDeleteSecret}
        />
      )}
    </div>
  );
}

export default SecretsSettingsScreen;
