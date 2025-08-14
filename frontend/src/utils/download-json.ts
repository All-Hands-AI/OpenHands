export const downloadJSON = (data: object, filename: string) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  try {
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    // Safely remove the link if still attached
    if (link.parentNode) {
      try {
        link.parentNode.removeChild(link);
      } catch {
        // no-op
      }
    } else if (typeof link.remove === "function") {
      // Fallback to Element.remove() (safe if not attached)
      link.remove();
    }
    URL.revokeObjectURL(url);
  }
};
