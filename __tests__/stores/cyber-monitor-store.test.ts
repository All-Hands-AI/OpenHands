import { beforeEach, describe, expect, it } from "vitest";
import {
  eventsToCsv,
  selectFilteredEvents,
  selectSeverityCounts,
  selectThreatLevel,
  selectTopIps,
  selectTopVectors,
  useCyberMonitorStore,
} from "#/stores/cyber-monitor-store";
import {
  MAX_THREAT_EVENTS,
  THREAT_ORIGINS,
} from "#/components/features/cyber-monitor/cyber-monitor-types";

const NOW = 1_700_000_000_000;
const seqRandom = (vals: number[]) => {
  let i = 0;
  return () => vals[i++ % vals.length] ?? 0.5;
};

describe("cyber monitor store", () => {
  beforeEach(() => {
    useCyberMonitorStore.getState().reset(NOW, seqRandom([0.1, 0.2, 0.05, 0.9]));
  });

  it("seeds events from the four origins targeting vintoai.com", () => {
    const { events } = useCyberMonitorStore.getState();
    expect(events.length).toBeGreaterThan(0);
    for (const e of events) {
      expect(THREAT_ORIGINS).toContain(e.origin);
      expect(e.targetAsset).toBe("vintoai.com");
      expect(e.sourceIp.startsWith(e.origin.ipPrefix)).toBe(true);
    }
  });

  it("ingest is a no-op while paused and resumes after toggle", () => {
    const s = useCyberMonitorStore.getState();
    s.togglePaused(NOW);
    const before = useCyberMonitorStore.getState().events.length;
    useCyberMonitorStore.getState().ingest(NOW + 1000, seqRandom([0.5]));
    expect(useCyberMonitorStore.getState().events).toHaveLength(before);
    useCyberMonitorStore.getState().togglePaused(NOW + 2000);
    useCyberMonitorStore.getState().ingest(NOW + 3000, seqRandom([0.5]));
    expect(useCyberMonitorStore.getState().events.length).toBeGreaterThan(before);
  });

  it("surge ingests three events per tick and unpauses", () => {
    const s = useCyberMonitorStore.getState();
    s.togglePaused(NOW);
    s.triggerSurge(NOW);
    expect(useCyberMonitorStore.getState().isPaused).toBe(false);
    const before = useCyberMonitorStore.getState().events.length;
    useCyberMonitorStore.getState().ingest(NOW + 1000, seqRandom([0.3, 0.6]));
    expect(useCyberMonitorStore.getState().events.length).toBe(before + 3);
  });

  it("caps events at MAX_THREAT_EVENTS", () => {
    for (let i = 0; i < MAX_THREAT_EVENTS + 20; i += 1) {
      useCyberMonitorStore.getState().ingest(NOW + i * 1000, seqRandom([0.4]));
    }
    expect(useCyberMonitorStore.getState().events.length).toBeLessThanOrEqual(
      MAX_THREAT_EVENTS,
    );
  });

  it("blockIp is idempotent, mitigates matching events, and is recorded once", () => {
    const ip = useCyberMonitorStore.getState().events[0]?.sourceIp ?? "1.2.3.4";
    useCyberMonitorStore.getState().blockIp(ip, NOW);
    useCyberMonitorStore.getState().blockIp(ip, NOW + 1);
    const s = useCyberMonitorStore.getState();
    expect(s.blockedIps.filter((x) => x === ip)).toHaveLength(1);
    for (const e of s.events.filter((x) => x.sourceIp === ip)) {
      expect(e.status).toBe("mitigated");
    }
  });

  it("filters by severity and search query", () => {
    const s = useCyberMonitorStore.getState();
    s.setSeverityFilter("critical");
    const filtered = selectFilteredEvents(useCyberMonitorStore.getState());
    expect(filtered.every((e) => e.severity === "critical")).toBe(true);
    s.setSeverityFilter("all");
    s.setSearchQuery("dubai");
    const byCity = selectFilteredEvents(useCyberMonitorStore.getState());
    expect(byCity.every((e) => e.origin.city === "Dubai")).toBe(true);
  });

  it("selectors aggregate severity, vectors, IPs and threat level", () => {
    const s = useCyberMonitorStore.getState();
    const counts = selectSeverityCounts(s);
    expect(
      counts.critical + counts.high + counts.medium + counts.low,
    ).toBe(s.events.length);
    expect(selectTopVectors(s).length).toBeGreaterThan(0);
    expect(selectTopIps(s).length).toBeGreaterThan(0);
    expect(["elevated", "high", "severe"]).toContain(selectThreatLevel(s, NOW));
  });

  it("exports CSV with header and escaped rows", () => {
    const s = useCyberMonitorStore.getState();
    const csv = eventsToCsv(s.events.slice(0, 2));
    const lines = csv.split("\n");
    expect(lines[0]).toContain("source_ip");
    expect(lines).toHaveLength(3);
    expect(lines[1]).toContain("vintoai.com");
  });
});
