export const getModels = async (): Promise<string[]> => {
  try {
    const response = await fetch("http://localhost:3000/api/options/models");
    return await response.json();
  } catch (error) {
    return [];
  }
};

export const getAgents = async (): Promise<string[]> => {
  try {
    const response = await fetch("http://localhost:3000/api/options/agents");
    return await response.json();
  } catch (error) {
    return [];
  }
};

export const retrieveFiles = async (token: string): Promise<string[]> => {
  const response = await fetch("/api/list-files", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.json();
};

export const retrieveFileContent = async (path: string): Promise<string> => {
  const url = new URL("http://localhost:3001/api/select-file");
  url.searchParams.append("file", path);
  const response = await fetch(url.toString());

  const data = await response.json();
  return data.code;
};
