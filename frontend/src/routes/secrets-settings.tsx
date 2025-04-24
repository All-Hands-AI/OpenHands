import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useGetSecrets } from "#/hooks/query/use-get-secrets";
import { useDeleteSecret } from "#/hooks/mutation/use-delete-secret";
import { SecretForm } from "#/components/features/settings/secrets-settings/secret-form";
import { SecretListItem } from "#/components/features/settings/secrets-settings/secret-list-item";

interface ConfirmationModalProps {
  onConfirm: () => void;
}

function ConfirmationModal({ onConfirm }: ConfirmationModalProps) {
  return (
    <div data-testid="confirmation-modal">
      <button data-testid="confirm-button" type="button" onClick={onConfirm}>
        Confirm
      </button>
    </div>
  );
}

function SecretsSettingsScreen() {
  const queryClient = useQueryClient();

  const { data: secrets } = useGetSecrets();
  const { mutate: deleteSecret } = useDeleteSecret();

  const [view, setView] = React.useState<
    "list" | "add-secret-form" | "edit-secret-form"
  >("list");
  const [selectedSecret, setSelectedSecret] = React.useState<string | null>(
    null,
  );
  const [confirmationModalIsVisible, setConfirmationModalIsVisible] =
    React.useState(false);

  const deleteSecretOptimistically = (secret: string) => {
    queryClient.setQueryData(
      ["secrets"],
      (oldSecrets: string[] | undefined) => {
        if (!oldSecrets) return [];
        return oldSecrets.filter((s) => s !== secret);
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

  return (
    <div data-testid="secrets-settings-screen">
      {secrets?.length === 0 && (
        <p data-testid="no-secrets-message">No secrets found</p>
      )}
      {view === "list" &&
        secrets?.map((secret) => (
          <SecretListItem
            key={secret}
            title={secret}
            onEdit={() => {
              setView("edit-secret-form");
              setSelectedSecret(secret);
            }}
            onDelete={() => {
              setConfirmationModalIsVisible(true);
              setSelectedSecret(secret);
            }}
          />
        ))}

      {(view === "add-secret-form" || view === "edit-secret-form") && (
        <SecretForm
          mode={view === "add-secret-form" ? "add" : "edit"}
          selectedSecret={selectedSecret}
          onSettled={() => setView("list")}
        />
      )}

      <button
        data-testid="add-secret-button"
        type="button"
        onClick={() => setView("add-secret-form")}
      >
        Add New Secret
      </button>

      {confirmationModalIsVisible && (
        <ConfirmationModal onConfirm={onConfirmDeleteSecret} />
      )}
    </div>
  );
}

export default SecretsSettingsScreen;
