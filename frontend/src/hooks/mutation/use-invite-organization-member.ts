import { useMutation, useQueryClient } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";

export const useInviteOrganizationMember = () => {
  const queryClient = useQueryClient();
  const { orgId } = useSelectedOrganizationId();

  return useMutation({
    mutationFn: ({ email }: { email: string }) =>
      organizationService.inviteMember({ orgId, email }),
    onSuccess: async (data) => {
      displaySuccessToast(`Invitation sent to ${data.email}`);
      await queryClient.invalidateQueries({
        queryKey: ["organizations", "members"],
      });
    },
  });
};
