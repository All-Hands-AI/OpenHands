export const base64ToBlob = (base64: string) => {
  // Remove the prefix (e.g. data:image/png;base64,)
  const base64WithoutPrefix = base64.split(",")[1];

  // Decode to bytes
  const bytes = atob(base64WithoutPrefix);

  // Create an array of byte values
  const byteNumbers = new Array(bytes.length);
  for (let i = 0; i < bytes.length; i += 1) {
    byteNumbers[i] = bytes.charCodeAt(i);
  }

  // Convert to Uint8Array
  const array = new Uint8Array(byteNumbers);

  // Create a Blob
  return new Blob([array], { type: "application/zip" });
};
