import { useEffect, useState } from "react";
import { useGetConfigQuery, useAuthenticateMutation } from "../api/slices";

export const useIsAuthed = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const { data: config } = useGetConfigQuery();
  const [authenticate] = useAuthenticateMutation();

  useEffect(() => {
    if (config) {
      authenticate({ appMode: config.APP_MODE })
        .unwrap()
        .then((authenticated) => {
          setIsAuthenticated(authenticated);
        })
        .catch(() => {
          setIsAuthenticated(false);
        });
    }
  }, [config, authenticate]);

  return { isAuthenticated };
};
