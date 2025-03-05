import { useAuth } from "#/context/auth-context";
import { useCurrentSettings } from "#/context/settings-context";
import { useConfig } from "./query/use-config";

export const useAppLogout = () => {
  const { data: config } = useConfig();
  const { logout } = useAuth();
  const { saveUserSettings } = useCurrentSettings();

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") logout();
    else await saveUserSettings({ unset_github_token: true });
  };

  return { handleLogout };
};
