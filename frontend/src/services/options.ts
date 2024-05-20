import { request } from "./api";

export async function fetchModels() {
  return request(`/api/options/models`);
}

export async function fetchAgents() {
  return request(`/api/options/agents`);
}
