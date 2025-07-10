import { useQuery } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useOrganization = ({ orgId }: { orgId: string }) =>
  useQuery({
    queryKey: ["organization", orgId, "about"],
    queryFn: () => organizationService.getOrganization({ orgId }),
  });
