import { redirect } from "@remix-run/react";

export const clientAction = () => {
  const token = localStorage.getItem("token");
  if (token) localStorage.removeItem("token");

  return redirect("/");
};
