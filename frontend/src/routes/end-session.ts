import { redirect } from "@remix-run/react";
import { clearSession } from "#/utils/clear-session";

export const clientAction = () => {
  clearSession();
  return redirect("/");
};
