const SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'] as const;

export function validateImageType(file: File): boolean {
  return SUPPORTED_IMAGE_TYPES.includes(file.type as typeof SUPPORTED_IMAGE_TYPES[number]);
}

export function getValidImageFiles(files: File[]): { validFiles: File[]; invalidFiles: File[] } {
  const validFiles: File[] = [];
  const invalidFiles: File[] = [];

  files.forEach((file) => {
    if (validateImageType(file)) {
      validFiles.push(file);
    } else {
      invalidFiles.push(file);
    }
  });

  return { validFiles, invalidFiles };
}
