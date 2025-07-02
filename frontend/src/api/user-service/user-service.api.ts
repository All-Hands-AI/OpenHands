import { OrganizationMember } from "#/types/org";
import { openHands } from "../open-hands-axios";

export const userService = {
  getUser: async () => {
    const { data } = await openHands.get<OrganizationMember>("/api/users/me");
    return data;
  },
};
