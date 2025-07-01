import { openHands } from "../open-hands-axios";

export const organizationService = {
  createOrganization: async ({ name }: { name: string }) => {
    const { data } = await openHands.post("/api/organizations", {
      name,
    });

    return data;
  },
};
