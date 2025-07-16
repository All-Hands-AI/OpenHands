import {
  Organization,
  OrganizationMember,
  OrganizationUserRole,
} from "#/types/org";
import { openHands } from "../open-hands-axios";

export const organizationService = {
  createOrganization: async ({ name }: { name: string }) => {
    const { data } = await openHands.post("/api/organizations", {
      name,
    });

    return data;
  },

  getOrganization: async ({ orgId }: { orgId: string }) => {
    const { data } = await openHands.get<Organization>(
      `/api/organizations/${orgId}`,
    );
    return data;
  },

  getOrganizations: async () => {
    const { data } = await openHands.get<Organization[]>("/api/organizations");
    return data;
  },

  updateOrganization: async ({
    orgId,
    name,
  }: {
    orgId: string;
    name: string;
  }) => {
    const { data } = await openHands.patch<Organization>(
      `/api/organizations/${orgId}`,
      { name },
    );
    return data;
  },

  deleteOrganization: async ({ orgId }: { orgId: string }) => {},

  getOrganizationMembers: async ({ orgId }: { orgId: string }) => {
    const { data } = await openHands.get<OrganizationMember[]>(
      `/api/organizations/${orgId}/members`,
    );
    return data;
  },

  getOrganizationPaymentInfo: async ({ orgId }: { orgId: string }) => {
    const { data } = await openHands.get<{
      cardNumber: string;
    }>(`/api/organizations/${orgId}/payment`);
    return data;
  },

  inviteMember: async ({ orgId, email }: { orgId: string; email: string }) => {
    const { data } = await openHands.post<OrganizationMember>(
      `/api/organizations/${orgId}/invite`,
      {
        email,
      },
    );

    return data;
  },

  updateMemberRole: async ({
    orgId,
    userId,
    role,
  }: {
    orgId: string;
    userId: string;
    role: OrganizationUserRole;
  }) => {
    const { data } = await openHands.patch(
      `/api/organizations/${orgId}/members`,
      {
        orgId,
        userId,
        role,
      },
    );

    return data;
  },
};
