import { json } from "@remix-run/react";
import OpenHands from "#/api/open-hands";
import { clearSession } from "#/utils/clear-session";

export const clientAction = async () => {
  await OpenHands.logout();
  clearSession();
  return json({ success: true });
};
