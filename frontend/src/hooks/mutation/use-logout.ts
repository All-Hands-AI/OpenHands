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
      setGitHubTokenIsSet(false);
      await queryClient.invalidateQueries();
      
      // Navigate to logout page
      navigate('/logout');
    },
  });
};
