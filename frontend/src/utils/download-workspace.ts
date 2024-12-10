import OpenHands from "#/api/open-hands";

/**
 * Downloads the current workspace as a .zip file.
 */
export const downloadWorkspace = async (conversationId: string) => {
  const blob = await OpenHands.getWorkspaceZip(conversationId);

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "workspace.zip");
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
};
