import { useMutation } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";

export const useCreateSecret = () =>
  useMutation({
    mutationFn: ({ name, value }: { name: string; value: string }) =>
      SecretsService.createSecret(name, value),
  });
