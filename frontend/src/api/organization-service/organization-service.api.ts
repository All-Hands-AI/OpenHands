import { OrganizationMember } from "#/types/org";
import { openHands } from "../open-hands-axios";

export const organizationService = {
  createOrganization: async ({ name }: { name: string }) => {
    const { data } = await openHands.post("/api/organizations", {
      name,
    });

    return data;
  },

  getOrganizationMembers: async () => {
    const { data } = await openHands.get<OrganizationMember[]>(
      "/api/organizations/members",
    );
    return data;
  },

  inviteMember: async ({ email }: { email: string }) => {
    const { data } = await openHands.post<OrganizationMember>(
      "/api/organizations/invite",
      {
        email,
      },
    );

    return data;
  },
};
