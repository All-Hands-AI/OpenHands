import { openHands } from "../open-hands-axios";
import { GitUser } from "#/types/git";

/**
 * User Service API - Handles all user-related API endpoints
 */
class UserService {
  /**
   * Get the current user's Git information
   * @returns Git user information
   */
  static async getUser(): Promise<GitUser> {
    const response = await openHands.get<GitUser>("/api/user/info");

    const { data } = response;

    const user: GitUser = {
      id: data.id,
      login: data.login,
      avatar_url: data.avatar_url,
      company: data.company,
      name: data.name,
      email: data.email,
    };

    return user;
  }
}

export default UserService;
