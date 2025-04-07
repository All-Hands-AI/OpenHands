import { useCurrentSettings } from "#/context/settings-context";
import { useLogout } from "./mutation/use-logout";
import { useConfig } from "./query/use-config";

export const useAppLogout = () => {
  const { data: config } = useConfig();
  const { mutateAsync: logout } = useLogout();
  const { saveUserSettings } = useCurrentSettings();

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") await logout();
    else await saveUserSettings({ unset_github_token: true });
  };

  return { handleLogout };
};
