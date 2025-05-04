import { openHands } from "./open-hands-axios";
import { Branch } from "#/types/git";

/**
 * Functions for working with repository branches
 */
export async function getRepositoryBranches(repository: string): Promise<Branch[]> {
  try {
    // The correct API endpoint URL based on the backend implementation
    const { data } = await openHands.get<Branch[]>(
      `/api/user/repository/${encodeURIComponent(repository)}/branches`
    );
    return data;
  } catch (error) {
    console.error("Error fetching repository branches:", error);
    return [];
  }
}
