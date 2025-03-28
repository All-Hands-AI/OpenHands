import { useLogout } from "./mutation/use-logout";

export const useAppLogout = () => {
  const { mutateAsync: logout } = useLogout();

  const handleLogout = async () => {
    await logout();
  };

  return { handleLogout };
};
