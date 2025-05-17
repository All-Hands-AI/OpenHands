export type JupyterLine = {
  type: "plaintext" | "image";
  content: string;
  url?: string;
};

const IMAGE_PREFIX = "![image](data:image/png;base64,";

export const parseCellContent = (content: string, imageUrls?: string[]) => {
  const lines: JupyterLine[] = [];
  let currentText = "";
  let imageUrlIndex = 0;

  for (const line of content.split("\n")) {
    if (line.startsWith(IMAGE_PREFIX)) {
      if (currentText) {
        lines.push({ type: "plaintext", content: currentText });
        currentText = ""; // Reset after pushing plaintext
      }

      // If we have image URLs available, use them
      const url =
        imageUrls && imageUrls.length > imageUrlIndex
          ? imageUrls[imageUrlIndex]
          : undefined;
      if (imageUrls && imageUrls.length > imageUrlIndex) {
        imageUrlIndex += 1;
      }
      lines.push({ type: "image", content: line, url });
    } else {
      currentText += `${line}\n`;
    }
  }

  if (currentText) {
    lines.push({ type: "plaintext", content: currentText });
  }

  return lines;
};
