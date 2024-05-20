import { request } from "./api";

export async function fetchModels() {
  console.log('fetch models');
  return request(`/api/options/models`);
}

export async function fetchAgents() {
  return request(`/api/options/agents`);
}
