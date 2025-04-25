import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useGetSecrets } from "#/hooks/query/use-get-secrets";
import { useDeleteSecret } from "#/hooks/mutation/use-delete-secret";
import { SecretForm } from "#/components/features/settings/secrets-settings/secret-form";
import { SecretListItem } from "#/components/features/settings/secrets-settings/secret-list-item";
import { BrandButton } from "#/components/features/settings/brand-button";

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
    <div
      data-testid="secrets-settings-screen"
      className="px-11 py-9 flex flex-col gap-5"
    >
      {secrets?.length === 0 && view === "list" && (
        <p data-testid="no-secrets-message">No secrets found</p>
      )}

      {view === "list" && (
        <ul>
          {secrets?.map((secret) => (
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
        </ul>
      )}

      {view === "list" && (
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
        <ConfirmationModal onConfirm={onConfirmDeleteSecret} />
      )}
    </div>
  );
}

export default SecretsSettingsScreen;
