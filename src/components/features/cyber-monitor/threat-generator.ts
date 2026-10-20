import {
  ATTACK_VECTORS,
  CYBER_MONITOR_ASSET,
  THREAT_ORIGINS,
  severityForRandom,
  type ThreatEvent,
} from "./cyber-monitor-types";

export type RandomFn = () => number;

const PORTS = [80, 443, 22, 3389, 8080, 53, 25, 3306] as const;

export function createThreatEvent(
  seq: number,
  now: number,
  random: RandomFn = Math.random,
): ThreatEvent {
  const origin =
    THREAT_ORIGINS[Math.floor(random() * THREAT_ORIGINS.length)] ??
    THREAT_ORIGINS[0];
  const vector =
    ATTACK_VECTORS[Math.floor(random() * ATTACK_VECTORS.length)] ??
    ATTACK_VECTORS[0];
  const octet = () => Math.floor(random() * 254) + 1;
  return {
    id: `threat-${seq}`,
    timestamp: now,
    severity: severityForRandom(random()),
    vector,
    origin,
    sourceIp: `${origin.ipPrefix}.${octet()}.${octet()}`,
    targetAsset: CYBER_MONITOR_ASSET,
    status: random() < 0.82 ? "blocked" : "monitoring",
    port: PORTS[Math.floor(random() * PORTS.length)] ?? 443,
    payloadKb: Math.round((random() * 480 + 4) * 10) / 10,
  };
}

export function seedThreatEvents(
  count: number,
  now: number,
  random: RandomFn = Math.random,
): ThreatEvent[] {
  return Array.from({ length: count }, (_, i) =>
    createThreatEvent(i + 1, now - (count - i) * 47_000, random),
  );
}
