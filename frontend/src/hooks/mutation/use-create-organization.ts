import { useMutation } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useCreateOrganization = () =>
  useMutation({
    mutationFn: ({ name }: { name: string }) =>
      organizationService.createOrganization({ name }),
  });
