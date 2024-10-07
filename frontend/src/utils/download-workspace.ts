import OpenHands from "#/api/open-hands";

/**
 * Downloads the current workspace as a .zip file.
 */
export const downloadWorkspace = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("No token found");
    }

    const blob = await OpenHands.getWorkspaceZip(token);

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "workspace.zip");
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  } catch (e) {
    console.error("Failed to download workspace as .zip", e);
  }
};
