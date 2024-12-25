import { useEffect, useState } from "react";
import { AppMode } from "#/types/app-mode";

export function useAppMode() {
  const [appMode, setAppMode] = useState<AppMode>(AppMode.OSS);

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((data) => {
        setAppMode(data.APP_MODE);
      })
      .catch((error) => {
        console.error("Error fetching app mode:", error);
      });
  }, []);

  return { appMode };
}
