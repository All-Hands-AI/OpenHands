import { redirect } from "@remix-run/react";

export const clientAction = () => {
  const token = localStorage.getItem("token");
  const repo = localStorage.getItem("repo");

  if (token) localStorage.removeItem("token");
  if (repo) localStorage.removeItem("repo");

  return redirect("/");
};
