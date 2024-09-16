const BASE_URL = "http://localhost:3000";

export const getModels = async (): Promise<string[]> => {
  const response = await fetch(`${BASE_URL}/api/options/models`);
  return response.json();
};

export const getAgents = async (): Promise<string[]> => {
  const response = await fetch(`${BASE_URL}/api/options/agents`);
  return response.json();
};

export const retrieveFiles = async (token: string): Promise<string[]> => {
  const response = await fetch(`${BASE_URL}/api/list-files`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.json();
};

export const retrieveFileContent = async (
  token: string,
  path: string,
): Promise<string> => {
  const url = new URL(`${BASE_URL}/api/select-file`);
  url.searchParams.append("file", path);
  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();
  return data.code;
};

export const saveFileContent = async (
  token: string,
  path: string,
  content: string,
) => {
  const response = await fetch(`${BASE_URL}/api/save-file`, {
    method: "POST",
    body: JSON.stringify({ filePath: path, content }),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  return response.json();
};

export interface Feedback {
  version: string;
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

export const sendFeedback = async (token: string, data: Feedback) => {
  const response = await fetch(`${BASE_URL}/api/submit-feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  return response.json();
};
