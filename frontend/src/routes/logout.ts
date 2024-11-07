import { json } from "@remix-run/react";
import { cache } from "#/utils/cache";

export const clientAction = () => {
  const ghToken = localStorage.getItem("ghToken");
  if (ghToken) localStorage.removeItem("ghToken");

  cache.clearAll();
  return json({ success: true });
};
