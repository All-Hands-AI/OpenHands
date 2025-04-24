import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { SecretsService } from "#/api/secrets-service";

function SecretsSettingsScreen() {
  const queryClient = useQueryClient();

  const { data: secrets } = useQuery({
    queryKey: ["secrets"],
    queryFn: SecretsService.getSecrets,
  });

  const { mutate: createSecret } = useMutation({
    mutationFn: ({ name, value }: { name: string; value: string }) =>
      SecretsService.createSecret(name, value),
  });

  const { mutate: updateSecret } = useMutation({
    mutationFn: ({
      secretToEdit,
      name,
      value,
    }: {
      secretToEdit: string;
      name: string;
      value: string;
    }) => SecretsService.updateSecret(secretToEdit, name, value),
  });

  const { mutate: deleteSecret } = useMutation({
    mutationFn: (id: string) => SecretsService.deleteSecret(id),
  });

  const [view, setView] = React.useState<
    "list" | "add-secret-form" | "edit-secret-form"
  >("list");
  const [selectedSecret, setSelectedSecret] = React.useState<string | null>(
    null,
  );
  const [confirmationModalIsVisible, setConfirmationModalIsVisible] =
    React.useState(false);

  const createSecretFormAction = (formData: FormData) => {
    const name = formData.get("secret-name")?.toString();
    const value = formData.get("secret-value")?.toString();

    if (name && value)
      createSecret({ name, value }, { onSuccess: () => setView("list") });
  };

  const updateSecretOptimistically = (oldName: string, name: string) => {
    queryClient.setQueryData(
      ["secrets"],
      (oldSecrets: string[] | undefined) => {
        if (!oldSecrets) return [];
        return oldSecrets.map((secret) => (secret === oldName ? name : secret));
      },
    );
  };

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

  const editSecretFormAction = (formData: FormData) => {
    const name = formData.get("secret-name")?.toString();
    const value = formData.get("secret-value")?.toString();

    if (selectedSecret && name && value) {
      updateSecretOptimistically(selectedSecret, name);
      updateSecret(
        { secretToEdit: selectedSecret, name, value },
        {
          onSettled: () => {
            setView("list");
          },
          onError: revertOptimisticUpdate,
        },
      );
    }
  };

  return (
    <div data-testid="secrets-settings-screen">
      {secrets?.length === 0 && (
        <p data-testid="no-secrets-message">No secrets found</p>
      )}
      {view === "list" &&
        secrets?.map((secret) => (
          <div key={secret} data-testid="secret-item">
            {secret}

            <button
              data-testid="edit-secret-button"
              type="button"
              onClick={() => {
                setView("edit-secret-form");
                setSelectedSecret(secret);
              }}
            >
              Edit Secret
            </button>

            <button
              data-testid="delete-secret-button"
              type="button"
              onClick={() => {
                setConfirmationModalIsVisible(true);
                setSelectedSecret(secret);
              }}
            >
              Delete Secret
            </button>
          </div>
        ))}

      {view === "add-secret-form" && (
        <form data-testid="add-secret-form" action={createSecretFormAction}>
          <input data-testid="name-input" name="secret-name" type="text" />
          <input data-testid="value-input" name="secret-value" type="text" />

          <button data-testid="submit-button" type="submit">
            Add new secret
          </button>
        </form>
      )}

      {view === "edit-secret-form" && (
        <form data-testid="edit-secret-form" action={editSecretFormAction}>
          <input data-testid="name-input" name="secret-name" type="text" />
          <input data-testid="value-input" name="secret-value" type="text" />

          <button data-testid="submit-button" type="submit">
            Add new secret
          </button>
        </form>
      )}

      <button
        data-testid="add-secret-button"
        type="button"
        onClick={() => setView("add-secret-form")}
      >
        Add New Secret
      </button>

      {confirmationModalIsVisible && (
        <div data-testid="confirmation-modal">
          <button
            data-testid="confirm-button"
            type="button"
            onClick={() => {
              if (selectedSecret) {
                deleteSecretOptimistically(selectedSecret);
                deleteSecret(selectedSecret, {
                  onSettled: () => {
                    setConfirmationModalIsVisible(false);
                  },
                });
              }
            }}
          >
            Confirm
          </button>
        </div>
      )}
    </div>
  );
}

export default SecretsSettingsScreen;
