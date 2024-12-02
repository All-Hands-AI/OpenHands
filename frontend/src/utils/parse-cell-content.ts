export type JupyterLine = { type: "plaintext" | "image"; content: string };

export const parseCellContent = (content: string) => {
  const lines: JupyterLine[] = [];
  let currentText = "";

  for (const line of content.split("\n")) {
    if (line.startsWith("![image](data:image/png;base64,")) {
      if (currentText) {
        lines.push({ type: "plaintext", content: currentText });
        currentText = ""; // Reset after pushing plaintext
      }
      lines.push({ type: "image", content: line });
    } else {
      currentText += `${line}\n`;
    }
  }

  if (currentText) {
    lines.push({ type: "plaintext", content: currentText });
  }

  return lines;
};
