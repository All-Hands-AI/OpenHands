export const base64ToBlob = (base64: string) => {
  // Remove the prefix (e.g. data:image/png;base64,)
  const base64WithoutPrefix = base64.split(",")[1] || base64;

  // Decode to bytes
  const bytes = atob(base64WithoutPrefix);

  // Process in chunks to avoid memory issues
  const chunkSize = 8192; // Process 8KB at a time
  const chunks = [];

  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.slice(i, i + chunkSize);
    const array = new Uint8Array(chunk.length);

    for (let j = 0; j < chunk.length; j += 1) {
      array[j] = chunk.charCodeAt(j);
    }

    chunks.push(array);
  }

  // Create a Blob from all chunks
  return new Blob(chunks, { type: "application/zip" });
};
