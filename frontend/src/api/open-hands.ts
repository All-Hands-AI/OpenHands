export const getModels = async () => {
  try {
    const response = await fetch("http://localhost:3000/api/options/models");
    return await response.json();
  } catch (error) {
    return ["openai/gpt-4o", "openai/gpt-3.5-turbo"];
  }
};

export const getAgents = async () => {
  try {
    const response = await fetch("http://localhost:3000/api/options/agents");
    return await response.json();
  } catch (error) {
    return ["CodeActAgent", "MonologueAgent", "DummyAgent"];
  }
};

export const retrieveFiles = async (): Promise<string[]> => {
  const response = await fetch("http://localhost:3000/api/list-files");
  return response.json();
};

export const retrieveFileContent = async (path: string): Promise<string> => {
  const url = new URL("http://localhost:3000/api/select-file");
  url.searchParams.append("file", path);
  const response = await fetch(url.toString());

  const data = await response.json();
  return data.code;
};
