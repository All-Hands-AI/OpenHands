import { useQuery } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useOrganizationMembers = () =>
  useQuery({
    queryKey: ["organizations", "members"],
    queryFn: () => organizationService.getOrganizationMembers({ orgId: "1" }),
  });
