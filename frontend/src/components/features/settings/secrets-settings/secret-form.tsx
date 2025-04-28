import { useQueryClient } from "@tanstack/react-query";
import { useCreateSecret } from "#/hooks/mutation/use-create-secret";
import { useUpdateSecret } from "#/hooks/mutation/use-update-secret";
import { SettingsInput } from "../settings-input";
import { cn } from "#/utils/utils";
import { BrandButton } from "../brand-button";

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

  const { mutate: createSecret } = useCreateSecret();
  const { mutate: updateSecret } = useUpdateSecret();

  const handleCreateSecret = (name: string, value: string) => {
    createSecret(
      { name, value },
      {
        onSettled: onCancel,
        onSuccess: async () => {
          await queryClient.invalidateQueries({ queryKey: ["secrets"] });
        },
      },
    );
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

  const revertOptimisticUpdate = () => {
    queryClient.invalidateQueries({ queryKey: ["secrets"] });
  };

  const handleEditSecret = (
    secretToEdit: string,
    name: string,
    value: string,
  ) => {
    updateSecretOptimistically(secretToEdit, name);
    updateSecret(
      { secretToEdit, name, value },
      {
        onSettled: onCancel,
        onError: revertOptimisticUpdate,
      },
    );
  };

  const formAction = (formData: FormData) => {
    const name = formData.get("secret-name")?.toString();
    const value = formData.get("secret-value")?.toString();

    if (name && value) {
      if (mode === "add") {
        handleCreateSecret(name, value);
      } else if (mode === "edit" && selectedSecret) {
        handleEditSecret(selectedSecret, name, value);
      }
    }
  };

  const formTestId = mode === "add" ? "add-secret-form" : "edit-secret-form";

  return (
    <form
      data-testid={formTestId}
      action={formAction}
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
          {mode === "add" && "Add secret"}
          {mode === "edit" && "Edit secret"}
        </BrandButton>
      </div>
    </form>
  );
}
