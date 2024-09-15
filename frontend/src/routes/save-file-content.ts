import { ClientActionFunctionArgs, json } from "@remix-run/react";
import { saveFileContent } from "#/api/open-hands";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const token = localStorage.getItem("token");
  const file = formData.get("file")?.toString();
  const content = formData.get("content")?.toString();

  if (token && file && content) {
    try {
      await saveFileContent(token, file, content);
      return json({ success: true });
    } catch (error) {
      return json({ success: false });
    }
  }

  return json({ success: false });
};
