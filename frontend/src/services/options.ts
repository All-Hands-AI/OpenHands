import { request } from "./api";

export async function fetchModels() {
  return await request(`/api/litellm-models`);
}

export async function fetchAgents() {
  return await request(`/api/agents`);
}
