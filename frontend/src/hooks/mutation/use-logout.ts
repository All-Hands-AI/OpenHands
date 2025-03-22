import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useLocation } from "react-router";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { saveLastPage } from "#/utils/last-page";

export const useLogout = () => {
  const { setGitHubTokenIsSet } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();

  return useMutation({
    mutationFn: OpenHands.logout,
    onSuccess: async () => {
      // Save current page if not on logout page
      if (!location.pathname.includes('/logout')) {
        saveLastPage();
      }
      
      setGitHubTokenIsSet(false);
      await queryClient.invalidateQueries();
      
      // Navigate to logout page
      navigate('/logout');
    },
  });
};
