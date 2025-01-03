export const sanitizeQuery = (query: string) =>
  query
    .replace(/https?:\/\//, "")
    .replace(/github.com\//, "")
    .replace(/\.git$/, "")
    .toLowerCase();
