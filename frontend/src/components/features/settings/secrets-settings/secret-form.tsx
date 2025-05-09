import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { useTranslation } from "react-i18next";
import { useCreateSecret } from "#/hooks/mutation/use-create-secret";
import { useUpdateSecret } from "#/hooks/mutation/use-update-secret";
import { SettingsInput } from "../settings-input";
import { cn } from "#/utils/utils";
import { BrandButton } from "../brand-button";
import { useGetSecrets } from "#/hooks/query/use-get-secrets";
import { GetSecretsResponse } from "#/api/secrets-service.types";
import { OptionalTag } from "../optional-tag";

interface SecretFormProps {
  mode: "add" | "edit";
  selectedSecret: string | null;
  onCancel: () => void;
}

export function SecretForm({
  mode,
  selectedSecret,
  onCancel,
}: SecretFormProps) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const { data: secrets } = useGetSecrets();
  const { mutate: createSecret } = useCreateSecret();
  const { mutate: updateSecret } = useUpdateSecret();

  const [error, setError] = React.useState<string | null>(null);

  const secretDescription =
    (mode === "edit" &&
      selectedSecret &&
      secrets
        ?.find((secret) => secret.name === selectedSecret)
        ?.description?.trim()) ||
    "";

  const handleCreateSecret = (
    name: string,
    value: string,
    description?: string,
  ) => {
    createSecret(
      { name, value, description },
      {
        onSettled: onCancel,
        onSuccess: async () => {
          await queryClient.invalidateQueries({ queryKey: ["secrets"] });
        },
      },
    );
  };

  const updateSecretOptimistically = (
    oldName: string,
    name: string,
    description?: string,
  ) => {
    queryClient.setQueryData<GetSecretsResponse["custom_secrets"]>(
      ["secrets"],
      (oldSecrets) => {
        if (!oldSecrets) return [];
        return oldSecrets.map((secret) => {
          if (secret.name === oldName) {
            return {
              ...secret,
              name,
              description,
            };
          }
          return secret;
        });
      },
    );
  };

  const revertOptimisticUpdate = () => {
    queryClient.invalidateQueries({ queryKey: ["secrets"] });
  };

  const handleEditSecret = (
    secretToEdit: string,
    name: string,
    description?: string,
  ) => {
    updateSecretOptimistically(secretToEdit, name, description);
    updateSecret(
      { secretToEdit, name, description },
      {
        onSettled: onCancel,
        onError: revertOptimisticUpdate,
      },
    );
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const name = formData.get("secret-name")?.toString();
    const value = formData.get("secret-value")?.toString().trim();
    const description = formData.get("secret-description")?.toString();

    if (name) {
      setError(null);

      const isNameAlreadyUsed = secrets?.some(
        (secret) => secret.name === name && secret.name !== selectedSecret,
      );
      if (isNameAlreadyUsed) {
        setError("Secret already exists");
        return;
      }

      if (mode === "add") {
        if (!value) {
          setError(t("SECRETS$SECRET_VALUE_REQUIRED"));
          return;
        }

        handleCreateSecret(name, value, description || undefined);
      } else if (mode === "edit" && selectedSecret) {
        handleEditSecret(selectedSecret, name, description || undefined);
      }
    }
  };

  const formTestId = mode === "add" ? "add-secret-form" : "edit-secret-form";

  return (
    <form
      data-testid={formTestId}
      onSubmit={handleSubmit}
      className="flex flex-col items-start gap-6"
    >
      <SettingsInput
        testId="name-input"
        name="secret-name"
        type="text"
        label="Name"
        className="w-[350px]"
        required
        defaultValue={mode === "edit" && selectedSecret ? selectedSecret : ""}
        placeholder="e.g. OpenAI_API_Key"
        pattern="^\S*$"
      />
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {mode === "add" && (
        <label className="flex flex-col gap-2.5 w-fit">
          <span className="text-sm">Value</span>
          <textarea
            data-testid="value-input"
            name="secret-value"
            required
            className={cn(
              "resize-none w-[680px]",
              "bg-tertiary border border-[#717888] rounded p-2 placeholder:italic placeholder:text-tertiary-alt",
              "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
            )}
            rows={8}
          />
        </label>
      )}

      <label className="flex flex-col gap-2.5 w-fit">
        <div className="flex items-center gap-2">
          <span className="text-sm">Description</span>
          <OptionalTag />
        </div>
        <input
          data-testid="description-input"
          name="secret-description"
          defaultValue={secretDescription}
          className={cn(
            "resize-none w-[680px]",
            "bg-tertiary border border-[#717888] rounded p-2 placeholder:italic placeholder:text-tertiary-alt",
            "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
          )}
        />
      </label>

      <div className="flex items-center gap-4">
        <BrandButton
          testId="cancel-button"
          type="button"
          variant="secondary"
          onClick={onCancel}
        >
          Cancel
        </BrandButton>
        <BrandButton testId="submit-button" type="submit" variant="primary">
          {mode === "add" && t("SECRETS$ADD_SECRET")}
          {mode === "edit" && t("SECRETS$EDIT_SECRET")}
        </BrandButton>
      </div>
    </form>
  );
}
