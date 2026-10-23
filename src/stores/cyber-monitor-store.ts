import { create } from "zustand";
import {
  BASE_BLOCKED_24H,
  MAX_CONSOLE_ENTRIES,
  MAX_THREAT_EVENTS,
  SURGE_DURATION_MS,
  THREAT_SEVERITIES,
  threatLevelForRate,
  type ConsoleEntry,
  type ThreatEvent,
  type ThreatLevel,
  type ThreatSeverity,
} from "#/components/features/cyber-monitor/cyber-monitor-types";
import {
  createThreatEvent,
  seedThreatEvents,
  type RandomFn,
} from "#/components/features/cyber-monitor/threat-generator";

export type SeverityFilter = ThreatSeverity | "all";

interface CyberMonitorState {
  events: ThreatEvent[];
  consoleEntries: ConsoleEntry[];
  blockedIps: string[];
  blocked24h: number;
  isPaused: boolean;
  surgeUntil: number | null;
  selectedThreatId: string | null;
  searchQuery: string;
  severityFilter: SeverityFilter;
  seq: number;
}

interface CyberMonitorActions {
  ingest: (now?: number, random?: RandomFn) => void;
  togglePaused: (now?: number) => void;
  triggerSurge: (now?: number) => void;
  selectThreat: (id: string | null) => void;
  blockIp: (ip: string, now?: number) => void;
  setSearchQuery: (q: string) => void;
  setSeverityFilter: (f: SeverityFilter) => void;
  reset: (now?: number, random?: RandomFn) => void;
}

export type CyberMonitorStore = CyberMonitorState & CyberMonitorActions;

const entry = (
  seq: number,
  now: number,
  kind: ConsoleEntry["kind"],
  messageKey: ConsoleEntry["messageKey"],
  ip?: string,
  vector?: string,
): ConsoleEntry => ({
  id: `console-${seq}`,
  timestamp: now,
  kind,
  messageKey,
  ip,
  vector,
});

function initialState(now: number, random: RandomFn): CyberMonitorState {
  const events = seedThreatEvents(18, now, random);
  return {
    events,
    consoleEntries: [entry(0, now, "info", "started")],
    blockedIps: [],
    blocked24h: BASE_BLOCKED_24H,
    isPaused: false,
    surgeUntil: null,
    selectedThreatId: null,
    searchQuery: "",
    severityFilter: "all",
    seq: events.length,
  };
}

export const useCyberMonitorStore = create<CyberMonitorStore>((set, get) => ({
  ...initialState(Date.now(), Math.random),
  ingest: (now = Date.now(), random = Math.random) => {
    const s = get();
    if (s.isPaused) return;
    const surging = s.surgeUntil !== null && now < s.surgeUntil;
    const count = surging ? 3 : 1;
    const fresh: ThreatEvent[] = [];
    let seq = s.seq;
    for (let i = 0; i < count; i += 1) {
      seq += 1;
      const e = createThreatEvent(seq, now, random);
      if (!s.blockedIps.includes(e.sourceIp)) fresh.push(e);
    }
    if (fresh.length === 0) return;
    const blockedDelta = fresh.filter((e) => e.status === "blocked").length;
    set({
      seq,
      events: [...fresh.reverse(), ...s.events].slice(0, MAX_THREAT_EVENTS),
      blocked24h: s.blocked24h + blockedDelta,
      surgeUntil:
        s.surgeUntil !== null && now >= s.surgeUntil ? null : s.surgeUntil,
      consoleEntries: [
        ...fresh.map((e, i) =>
          entry(seq + i, now, "block", "blocked", e.sourceIp, e.vector),
        ),
        ...s.consoleEntries,
      ].slice(0, MAX_CONSOLE_ENTRIES),
    });
  },
  togglePaused: (now = Date.now()) => {
    const s = get();
    set({
      isPaused: !s.isPaused,
      consoleEntries: [
        entry(
          s.seq + 1000 + s.consoleEntries.length,
          now,
          "info",
          s.isPaused ? "resumed" : "paused",
        ),
        ...s.consoleEntries,
      ].slice(0, MAX_CONSOLE_ENTRIES),
    });
  },
  triggerSurge: (now = Date.now()) => {
    const s = get();
    set({
      surgeUntil: now + SURGE_DURATION_MS,
      isPaused: false,
      consoleEntries: [
        entry(s.seq + 2000 + s.consoleEntries.length, now, "surge", "surge"),
        ...s.consoleEntries,
      ].slice(0, MAX_CONSOLE_ENTRIES),
    });
  },
  selectThreat: (id) => set({ selectedThreatId: id }),
  blockIp: (ip, now = Date.now()) => {
    const s = get();
    if (s.blockedIps.includes(ip)) return;
    set({
      blockedIps: [...s.blockedIps, ip],
      events: s.events.map((e) =>
        e.sourceIp === ip ? { ...e, status: "mitigated" as const } : e,
      ),
      consoleEntries: [
        entry(
          s.seq + 3000 + s.consoleEntries.length,
          now,
          "warn",
          "ip_blocked",
          ip,
        ),
        ...s.consoleEntries,
      ].slice(0, MAX_CONSOLE_ENTRIES),
    });
  },
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setSeverityFilter: (severityFilter) => set({ severityFilter }),
  reset: (now = Date.now(), random = Math.random) =>
    set(initialState(now, random)),
}));

// Selectors — pure, testable, single source of truth derived from events.
export function selectFilteredEvents(s: CyberMonitorState): ThreatEvent[] {
  const q = s.searchQuery.trim().toLowerCase();
  return s.events.filter((e) => {
    if (s.severityFilter !== "all" && e.severity !== s.severityFilter)
      return false;
    if (s.blockedIps.includes(e.sourceIp)) return true; // still show history
    if (!q) return true;
    return [e.sourceIp, e.vector, e.origin.country, e.origin.city, e.id]
      .join(" ")
      .toLowerCase()
      .includes(q);
  });
}

export function selectAttackRatePerMin(
  s: CyberMonitorState,
  now = Date.now(),
): number {
  const windowMs = 60_000;
  const recent = s.events.filter((e) => now - e.timestamp < windowMs).length;
  // Seed events span longer than a minute; fall back to density estimate.
  if (recent > 0) return recent;
  return s.events.length === 0 ? 0 : Math.min(12, s.events.length);
}

export function selectThreatLevel(
  s: CyberMonitorState,
  now?: number,
): ThreatLevel {
  return threatLevelForRate(selectAttackRatePerMin(s, now));
}

export function selectSeverityCounts(
  s: CyberMonitorState,
): Record<ThreatSeverity, number> {
  const counts: Record<ThreatSeverity, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  for (const e of s.events) counts[e.severity] += 1;
  return counts;
}

export function selectTopVectors(
  s: CyberMonitorState,
  limit = 5,
): { vector: string; count: number }[] {
  const map = new Map<string, number>();
  for (const e of s.events) map.set(e.vector, (map.get(e.vector) ?? 0) + 1);
  return [...map.entries()]
    .map(([vector, count]) => ({ vector, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

export function selectTopIps(
  s: CyberMonitorState,
  limit = 5,
): { ip: string; count: number; country: string }[] {
  const map = new Map<string, { count: number; country: string }>();
  for (const e of s.events) {
    const cur = map.get(e.sourceIp) ?? { count: 0, country: e.origin.country };
    cur.count += 1;
    map.set(e.sourceIp, cur);
  }
  return [...map.entries()]
    .map(([ip, v]) => ({ ip, ...v }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

export function selectSelectedThreat(s: CyberMonitorState): ThreatEvent | null {
  return s.events.find((e) => e.id === s.selectedThreatId) ?? null;
}

export { THREAT_SEVERITIES };

export function eventsToCsv(events: ThreatEvent[]): string {
  const header =
    "id,timestamp,severity,vector,source_ip,country,city,asn,target,port,status";
  const esc = (v: string | number) => {
    const str = String(v);
    return /[",\n]/.test(str) ? `"${str.replaceAll('"', '""')}"` : str;
  };
  const rows = events.map((e) =>
    [
      e.id,
      new Date(e.timestamp).toISOString(),
      e.severity,
      e.vector,
      e.sourceIp,
      e.origin.country,
      e.origin.city,
      e.origin.asn,
      e.targetAsset,
      e.port,
      e.status,
    ]
      .map(esc)
      .join(","),
  );
  return [header, ...rows].join("\n");
}
