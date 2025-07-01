import { useMutation } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useInviteOrganizationMember = () =>
  useMutation({
    mutationFn: ({ email }: { email: string }) =>
      organizationService.inviteMember({ email }),
  });
