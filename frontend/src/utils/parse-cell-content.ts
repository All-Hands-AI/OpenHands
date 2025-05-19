export type JupyterLine = {
  type: "plaintext" | "image";
  content: string;
  url?: string;
};

export const parseCellContent = (content: string, imageUrls?: string[]) => {
  const lines: JupyterLine[] = [];
  let currentText = "";

  // First, process the text content
  for (const line of content.split("\n")) {
    currentText += `${line}\n`;
  }

  if (currentText) {
    lines.push({ type: "plaintext", content: currentText });
  }

  // Then, add image lines if we have image URLs
  if (imageUrls && imageUrls.length > 0) {
    imageUrls.forEach((url) => {
      lines.push({
        type: "image",
        content: `![image](${url})`,
        url,
      });
    });
  }

  return lines;
};
