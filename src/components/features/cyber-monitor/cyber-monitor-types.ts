export type ThreatSeverity = "critical" | "high" | "medium" | "low";
export type ThreatStatus = "blocked" | "monitoring" | "mitigated";
export type ThreatLevel = "elevated" | "high" | "severe";
export type OriginCountryCode = "AE" | "IL" | "IN" | "BT";

export const THREAT_SEVERITIES: readonly ThreatSeverity[] = [
  "critical",
  "high",
  "medium",
  "low",
];

export const CYBER_MONITOR_ASSET = "vintoai.com";
export const CYBER_MONITOR_TARGET = {
  city: "Lahore",
  country: "Pakistan",
  lat: 31.5204,
  lon: 74.3587,
} as const;

export interface ThreatOrigin {
  countryCode: OriginCountryCode;
  country: string;
  city: string;
  asn: string;
  ipPrefix: string;
  lat: number;
  lon: number;
}

export const THREAT_ORIGINS: readonly ThreatOrigin[] = [
  {
    countryCode: "AE",
    country: "UAE",
    city: "Dubai",
    asn: "AS13335",
    ipPrefix: "185.93",
    lat: 25.2048,
    lon: 55.2708,
  },
  {
    countryCode: "IL",
    country: "Israel",
    city: "Tel Aviv",
    asn: "AS20940",
    ipPrefix: "45.148",
    lat: 32.0853,
    lon: 34.7818,
  },
  {
    countryCode: "IN",
    country: "India",
    city: "Mumbai",
    asn: "AS24560",
    ipPrefix: "103.42",
    lat: 19.076,
    lon: 72.8777,
  },
  {
    countryCode: "BT",
    country: "Bhutan",
    city: "Thimphu",
    asn: "AS17660",
    ipPrefix: "202.144",
    lat: 27.4728,
    lon: 89.6393,
  },
];

export const ATTACK_VECTORS = [
  "DDoS",
  "SQL Injection",
  "XSS",
  "Brute Force",
  "Port Scan",
  "Malware C2",
  "Phishing",
  "Ransomware Probe",
] as const;
export type AttackVector = (typeof ATTACK_VECTORS)[number];

export interface ThreatEvent {
  id: string;
  timestamp: number;
  severity: ThreatSeverity;
  vector: AttackVector;
  origin: ThreatOrigin;
  sourceIp: string;
  targetAsset: string;
  status: ThreatStatus;
  port: number;
  payloadKb: number;
}

export interface ConsoleEntry {
  id: string;
  timestamp: number;
  kind: "info" | "warn" | "block" | "surge";
  messageKey: ConsoleMessageKey;
  ip?: string;
  vector?: string;
}

export type ConsoleMessageKey =
  | "started"
  | "blocked"
  | "surge"
  | "paused"
  | "resumed"
  | "ip_blocked";

export const MAX_THREAT_EVENTS = 120;
export const MAX_CONSOLE_ENTRIES = 60;
export const BASE_BLOCKED_24H = 1284;
export const TICK_INTERVAL_MS = 2200;
export const SURGE_DURATION_MS = 15000;
export const SEVERITY_WEIGHTS: Record<ThreatSeverity, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export function threatLevelForRate(ratePerMin: number): ThreatLevel {
  if (ratePerMin >= 40) return "severe";
  if (ratePerMin >= 18) return "high";
  return "elevated";
}

export function severityForRandom(r: number): ThreatSeverity {
  if (r < 0.14) return "critical";
  if (r < 0.42) return "high";
  if (r < 0.74) return "medium";
  return "low";
}
