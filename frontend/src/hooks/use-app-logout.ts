import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useSaveSettings } from "./mutation/use-save-settings";
import { useConfig } from "./query/use-config";
import { useAuth } from "#/context/auth-context";

export const useAppLogout = () => {
  const { data: config } = useConfig();
  const { mutate: saveUserSettings } = useSaveSettings();
  const { setGitHubTokenIsSet } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") {
      navigate("/logout");
    } else {
      saveUserSettings({ unset_github_token: true });
      setGitHubTokenIsSet(false);
      localStorage.removeItem("gh_token");
      posthog.reset();
      navigate("/");
    }
  };

  return { handleLogout };
};
