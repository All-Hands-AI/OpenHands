import { useAuth } from "#/context/auth-context";

/**
 * A hook that returns whether the user is likely authenticated based on local state.
 * This is used to prevent unnecessary API calls when the user is not logged in.
 */
export const useAuthState = () => {
  const { providersAreSet } = useAuth();
  
  // If providers are set, the user is likely authenticated
  return providersAreSet;
};