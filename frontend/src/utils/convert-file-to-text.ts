export const convertFileToText = async (file: File) => {
  const reader = new FileReader();

  return new Promise<string>((resolve) => {
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.readAsText(file);
  });
};
