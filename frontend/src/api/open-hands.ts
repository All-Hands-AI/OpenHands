export const getModels = async () => {
  try {
    const response = await fetch("/api/options/models");
    return await response.json();
  } catch (error) {
    return ["openai/gpt-4o", "openai/gpt-3.5-turbo"];
  }
};

export const getAgents = async () => {
  try {
    const response = await fetch("/api/options/agents");
    return await response.json();
  } catch (error) {
    return ["CodeActAgent", "MonologueAgent", "DummyAgent"];
  }
};
