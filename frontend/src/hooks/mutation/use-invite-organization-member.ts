import { useMutation, useQueryClient } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useInviteOrganizationMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email }: { email: string }) =>
      organizationService.inviteMember({ email }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["organization", "members"],
      });
    },
  });
};
