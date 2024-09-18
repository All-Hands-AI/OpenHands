import { json } from "@remix-run/react";

export const clientAction = () => {
  const ghToken = localStorage.getItem("ghToken");
  if (ghToken) localStorage.removeItem("ghToken");

  return json({ success: true });
};
