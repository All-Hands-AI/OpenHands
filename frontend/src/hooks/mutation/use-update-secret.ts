import { useMutation } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";

export const useUpdateSecret = () =>
  useMutation({
    mutationFn: ({
      secretToEdit,
      name,
    }: {
      secretToEdit: string;
      name: string;
    }) => SecretsService.updateSecret(secretToEdit, name),
  });
