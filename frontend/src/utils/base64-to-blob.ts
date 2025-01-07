export const base64ToBlob = (base64: string) => {
  // Remove the prefix (e.g. data:image/png;base64,)
  const base64WithoutPrefix = base64.split(",")[1];
  console.log('blobbing base64WithoutPrefix', base64WithoutPrefix);

  // Decode to bytes
  const bytes = atob(base64WithoutPrefix);
  console.log('bytes', bytes);

  // Create an array of byte values
  const byteNumbers = new Array(bytes.length);
  console.log('byteNumbers', byteNumbers);
  for (let i = 0; i < bytes.length; i += 1) {
    byteNumbers[i] = bytes.charCodeAt(i);
  }
  console.log('byteNumbers', byteNumbers);

  // Convert to Uint8Array
  const array = new Uint8Array(byteNumbers);

  // Create a Blob
  return new Blob([array], { type: "application/zip" });
};
