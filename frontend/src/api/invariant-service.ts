import { openHands } from "./open-hands-axios";

class InvariantService {
  static async getPolicy() {
    const { data } = await openHands.get("/api/security/policy");
    return data.policy;
  }

  static async getRiskSeverity() {
    const { data } = await openHands.get("/api/security/settings");
    return data.RISK_SEVERITY;
  }

  static async getTraces() {
    const { data } = await openHands.get("/api/security/export-trace");
    return data;
  }

  static async updatePolicy(policy: string) {
    await openHands.post("/api/security/policy", { policy });
  }

  static async updateRiskSeverity(riskSeverity: number) {
    await openHands.post("/api/security/settings", {
      RISK_SEVERITY: riskSeverity,
    });
  }
}

export default InvariantService;
