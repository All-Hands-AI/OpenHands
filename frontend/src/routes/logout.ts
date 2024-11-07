import { json } from "@remix-run/react";
import posthog from "posthog-js";
import { cache } from "#/utils/cache";

export const clientAction = () => {
  const ghToken = localStorage.getItem("ghToken");
  if (ghToken) localStorage.removeItem("ghToken");

  cache.clearAll();
  posthog.reset();

  return json({ success: true });
};
