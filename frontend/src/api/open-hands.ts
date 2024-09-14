export const getModels = async (): Promise<string[]> => {
  try {
    const response = await fetch(`http://localhost:3000/api/options/models`);
    return await response.json();
  } catch (error) {
    return [];
  }
};

export const getAgents = async (): Promise<string[]> => {
  try {
    const response = await fetch(`http://localhost:3000/api/options/agents`);
    return await response.json();
  } catch (error) {
    return [];
  }
};

export const retrieveFiles = async (token: string): Promise<string[]> => {
  const response = await fetch(`/api/list-files`, {
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
  const url = new URL(`http://localhost:3001/api/select-file`);
  url.searchParams.append("file", path);
  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();
  return data.code;
};

export interface Feedback {
  version: string;
  email: string;
  token: string;
  feedback: "positive" | "negative";
  permissions: "public" | "private";
  trajectory: unknown[];
}

export const sendFeedback = async (data: Feedback) => {
  const response = await fetch("http://localhost:3000/api/submit-feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return response.json();
};
