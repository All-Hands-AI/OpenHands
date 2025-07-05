import { useQuery } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useOrganizationMembers = () =>
  useQuery({
    queryKey: ["organization", "members"],
    queryFn: organizationService.getOrganizationMembers,
  });
