import OpenHands from "#/api/open-hands";

/**
 * Downloads the current workspace as a .zip file.
 */
export const downloadWorkspace = async () => {
  const response = await OpenHands.getWorkspaceZip();

  // Extract filename from response headers
  let filename = "workspace.zip";
  const disposition = response.headers.get("Content-Disposition");
  if (disposition && disposition.indexOf('filename=') !== -1) {
    const matches = /filename="?([^"]+)"?/.exec(disposition);
    if (matches != null && matches[1]) {
      filename = matches[1];
    }
  }

  // Get the response as a blob
  const blob = await response.blob();

  // Create download link and trigger download with extracted filename
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
};
