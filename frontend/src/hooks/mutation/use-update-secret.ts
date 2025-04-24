import { useMutation } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";

export const useUpdateSecret = () =>
  useMutation({
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
