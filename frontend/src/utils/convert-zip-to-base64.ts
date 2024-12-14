export const convertZipToBase64 = async (file: File) => {
  const reader = new FileReader();

  return new Promise<string>((resolve) => {
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.readAsDataURL(file);
  });
};
