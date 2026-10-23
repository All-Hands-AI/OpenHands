import React from "react";
import { useTranslation } from "react-i18next";
import { Shield } from "lucide-react";
import { I18nKey } from "#/i18n/declaration";
import { useTracking } from "#/hooks/use-tracking";
import {
  eventsToCsv,
  selectAttackRatePerMin,
  selectFilteredEvents,
  selectSelectedThreat,
  selectSeverityCounts,
  selectThreatLevel,
  selectTopIps,
  selectTopVectors,
  useCyberMonitorStore,
} from "#/stores/cyber-monitor-store";
import {
  CYBER_MONITOR_ASSET,
  TICK_INTERVAL_MS,
  type ThreatLevel,
} from "./cyber-monitor-types";
import { CyberAttackMap } from "./cyber-attack-map";
import { KpiCard, RankedList, SeverityDonut } from "./cyber-monitor-panels";
import { CyberThreatFeed } from "./cyber-threat-feed";
import { CyberThreatDrawer } from "./cyber-threat-drawer";
import { CyberSocConsole } from "./cyber-soc-console";

function levelLabelKey(level: ThreatLevel) {
  switch (level) {
    case "severe":
      return I18nKey.CYBER_MONITOR$LEVEL_SEVERE;
    case "high":
      return I18nKey.CYBER_MONITOR$LEVEL_HIGH;
    case "elevated":
      return I18nKey.CYBER_MONITOR$LEVEL_ELEVATED;
  }
}

export function CyberMonitor() {
  const { t } = useTranslation("openhands");
  const { trackCyberMonitorAction } = useTracking();
  const state = useCyberMonitorStore();
  const trackedRef = React.useRef(false);

  React.useEffect(() => {
    if (trackedRef.current) return;
    trackedRef.current = true;
    trackCyberMonitorAction({ action: "viewed" });
  }, []);

  React.useEffect(() => {
    const id = setInterval(() => {
      useCyberMonitorStore.getState().ingest();
    }, TICK_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  const filtered = selectFilteredEvents(state);
  const counts = selectSeverityCounts(state);
  const rate = selectAttackRatePerMin(state);
  const level = selectThreatLevel(state);
  const selected = selectSelectedThreat(state);
  const [nowMs, setNowMs] = React.useState(() => Date.now());
  React.useEffect(() => {
    const id = setInterval(() => setNowMs(Date.now()), TICK_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);
  const surging = state.surgeUntil !== null && nowMs < state.surgeUntil;

  const exportCsv = () => {
    const blob = new Blob([eventsToCsv(filtered)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cyber-monitor-threats.csv";
    a.click();
    URL.revokeObjectURL(url);
    trackCyberMonitorAction({ action: "exported_csv" });
  };

  return (
    <div
      data-testid="cyber-monitor"
      className="mx-auto max-w-7xl space-y-4 p-4 md:p-6"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Shield className="size-8 text-red-400" aria-hidden />
          <div>
            <h1 className="text-xl font-bold text-content">
              {t(I18nKey.CYBER_MONITOR$TITLE)}
            </h1>
            <p className="text-sm text-muted">
              {t(I18nKey.CYBER_MONITOR$SUBTITLE)} · {CYBER_MONITOR_ASSET}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            data-testid="cyber-pause-toggle"
            onClick={() => {
              state.togglePaused();
              trackCyberMonitorAction({
                action: state.isPaused ? "resumed" : "paused",
              });
            }}
            className="rounded-md border border-border px-3 py-2 text-sm text-content"
          >
            {state.isPaused
              ? t(I18nKey.CYBER_MONITOR$RESUME)
              : t(I18nKey.CYBER_MONITOR$PAUSE)}
          </button>
          <button
            type="button"
            data-testid="cyber-surge"
            onClick={() => {
              state.triggerSurge();
              trackCyberMonitorAction({ action: "surge_triggered" });
            }}
            className="rounded-md border border-orange-500/40 px-3 py-2 text-sm text-orange-400"
          >
            {t(I18nKey.CYBER_MONITOR$SURGE)}
            {surging ? (
              <span
                aria-hidden
                className="ml-1.5 inline-block size-2 rounded-full bg-current align-middle"
              />
            ) : null}
          </button>
          <button
            type="button"
            data-testid="cyber-export"
            onClick={exportCsv}
            className="rounded-md border border-border px-3 py-2 text-sm text-content"
          >
            {t(I18nKey.CYBER_MONITOR$EXPORT_CSV)}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label={t(I18nKey.CYBER_MONITOR$BLOCKED_24H)}
          value={String(state.blocked24h)}
          testId="cyber-kpi-blocked"
        />
        <KpiCard
          label={t(I18nKey.CYBER_MONITOR$ATTACK_RATE)}
          value={String(rate)}
          testId="cyber-kpi-rate"
        />
        <KpiCard
          label={t(I18nKey.CYBER_MONITOR$THREAT_LEVEL)}
          value={t(levelLabelKey(level))}
          testId="cyber-kpi-level"
        />
        <KpiCard
          label={t(I18nKey.CYBER_MONITOR$ASSET_STATUS)}
          value={t(I18nKey.CYBER_MONITOR$STATUS_PROTECTED)}
          testId="cyber-kpi-status"
        />
      </div>

      <CyberAttackMap events={state.events} />

      <div className="grid gap-4 lg:grid-cols-3">
        <SeverityDonut counts={counts} total={state.events.length} />
        <RankedList
          title={t(I18nKey.CYBER_MONITOR$TOP_VECTORS)}
          testId="cyber-top-vectors"
          rows={selectTopVectors(state).map((r) => ({
            label: r.vector,
            count: r.count,
          }))}
        />
        <RankedList
          title={t(I18nKey.CYBER_MONITOR$TOP_IPS)}
          testId="cyber-top-ips"
          rows={selectTopIps(state).map((r) => ({
            label: r.ip,
            sub: r.country,
            count: r.count,
          }))}
        />
      </div>

      <CyberThreatFeed
        events={filtered}
        searchQuery={state.searchQuery}
        severityFilter={state.severityFilter}
        onSearchChange={state.setSearchQuery}
        onFilterChange={state.setSeverityFilter}
        onSelect={(e) => {
          state.selectThreat(e.id);
          trackCyberMonitorAction({
            action: "threat_opened",
            severity: e.severity,
          });
        }}
      />

      <CyberSocConsole entries={state.consoleEntries} />

      {selected ? (
        <CyberThreatDrawer
          threat={selected}
          isBlocked={state.blockedIps.includes(selected.sourceIp)}
          onClose={() => state.selectThreat(null)}
          onBlockIp={(ip) => {
            state.blockIp(ip);
            trackCyberMonitorAction({
              action: "ip_blocked",
              severity: selected.severity,
            });
          }}
        />
      ) : null}
    </div>
  );
}
