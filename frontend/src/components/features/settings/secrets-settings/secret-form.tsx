import { useQueryClient } from "@tanstack/react-query";
import { useCreateSecret } from "#/hooks/mutation/use-create-secret";
import { useUpdateSecret } from "#/hooks/mutation/use-update-secret";

interface SecretFormProps {
  mode: "add" | "edit";
  selectedSecret: string | null;
  onSettled?: () => void;
}

export function SecretForm({
  mode,
  selectedSecret,
  onSettled,
}: SecretFormProps) {
  const queryClient = useQueryClient();

  const { mutate: createSecret } = useCreateSecret();
  const { mutate: updateSecret } = useUpdateSecret();

  const handleCreateSecret = (name: string, value: string) => {
    createSecret({ name, value }, { onSettled });
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
        onSettled,
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
    <form data-testid={formTestId} action={formAction}>
      <input data-testid="name-input" name="secret-name" type="text" />
      <input data-testid="value-input" name="secret-value" type="text" />

      <button data-testid="submit-button" type="submit">
        Add new secret
      </button>
    </form>
  );
}
