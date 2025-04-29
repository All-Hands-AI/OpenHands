export type CustomSecret = {
  name: string;
  value: string;
  description?: string;
};

export interface GetSecretsResponse {
  custom_secrets: Omit<CustomSecret, "value">[];
}
