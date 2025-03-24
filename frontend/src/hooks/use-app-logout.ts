import { useLogout } from "./mutation/use-logout";
import { useSaveSettings } from "./mutation/use-save-settings";
import { useConfig } from "./query/use-config";

export const useAppLogout = () => {
  const { data: config } = useConfig();
  const { mutateAsync: logout } = useLogout();
  const { mutate: saveUserSettings } = useSaveSettings();

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") await logout();
    else saveUserSettings({ unset_github_token: true });
  };

  return { handleLogout };
};
