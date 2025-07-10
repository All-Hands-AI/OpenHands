import { useQuery } from "@tanstack/react-query";
import { organizationService } from "#/api/organization-service/organization-service.api";

export const useOrganizationPaymentInfo = ({ orgId }: { orgId: string }) =>
  useQuery({
    queryKey: ["organization", orgId, "payment"],
    queryFn: () => organizationService.getOrganizationPaymentInfo({ orgId }),
  });
