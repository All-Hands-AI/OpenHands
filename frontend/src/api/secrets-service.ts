import { openHands } from "./open-hands-axios";

export class SecretsService {
  static async getSecrets() {
    const { data } = await openHands.get<{ custom_secrets: string[] }>(
      "/api/secrets",
    );

    return data.custom_secrets;
  }

  static async createSecret(name: string, value: string) {
    const { data } = await openHands.post<boolean>("/api/secrets", {
      custom_secrets: { [name]: { secret: value } },
    });

    return data;
  }

  static async updateSecret(id: string, name: string, value: string) {
    const { data } = await openHands.put<boolean>(`/api/secrets/${id}`, {
      custom_secrets: { [name]: { value } },
    });

    return data;
  }

  static async deleteSecret(id: string) {
    const { data } = await openHands.delete<boolean>(`/api/secrets/${id}`);
    return data;
  }
}
