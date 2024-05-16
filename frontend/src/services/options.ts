import { request } from "./api";

export async function fetchModels() {
  return request(`/api/litellm-models`);
}

export async function fetchAgents() {
  return request(`/api/agents`);
}
