import { json } from "@remix-run/react";
import posthog from "posthog-js";

export const clientAction = () => {
  const ghToken = localStorage.getItem("ghToken");
  if (ghToken) localStorage.removeItem("ghToken");

  posthog.reset();

  return json({ success: true });
};
