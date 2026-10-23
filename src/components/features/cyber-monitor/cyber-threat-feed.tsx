import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { THREAT_SEVERITIES, type ThreatEvent } from "./cyber-monitor-types";
import { SEVERITY_BADGE_CLASS, severityLabelKey } from "./cyber-monitor-panels";
import type { SeverityFilter } from "#/stores/cyber-monitor-store";

export function statusLabelKey(status: ThreatEvent["status"]) {
  switch (status) {
    case "blocked":
      return I18nKey.CYBER_MONITOR$STATUS_BLOCKED;
    case "monitoring":
      return I18nKey.CYBER_MONITOR$STATUS_MONITORING;
    case "mitigated":
      return I18nKey.CYBER_MONITOR$STATUS_MITIGATED;
  }
}

export function CyberThreatFeed({
  events,
  searchQuery,
  severityFilter,
  onSearchChange,
  onFilterChange,
  onSelect,
}: {
  events: ThreatEvent[];
  searchQuery: string;
  severityFilter: SeverityFilter;
  onSearchChange: (v: string) => void;
  onFilterChange: (v: SeverityFilter) => void;
  onSelect: (e: ThreatEvent) => void;
}) {
  const { t } = useTranslation("openhands");
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="mb-3 text-sm font-semibold text-content">
        {t(I18nKey.CYBER_MONITOR$LIVE_FEED)}
      </h2>
      <div className="mb-3 flex flex-wrap gap-2">
        <input
          data-testid="cyber-search"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={t(I18nKey.CYBER_MONITOR$SEARCH_PLACEHOLDER)}
          className="min-w-52 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-content"
        />
        <select
          data-testid="cyber-severity-filter"
          value={severityFilter}
          onChange={(e) => onFilterChange(e.target.value as SeverityFilter)}
          aria-label={t(I18nKey.CYBER_MONITOR$FILTER_ALL)}
          className="rounded-md border border-border bg-background px-3 py-2 text-sm text-content"
        >
          <option value="all">{t(I18nKey.CYBER_MONITOR$FILTER_ALL)}</option>
          {THREAT_SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {t(severityLabelKey(s))}
            </option>
          ))}
        </select>
      </div>
      {events.length === 0 ? (
        <p
          className="py-6 text-center text-sm text-muted"
          data-testid="cyber-no-results"
        >
          {t(I18nKey.CYBER_MONITOR$NO_RESULTS)}
        </p>
      ) : (
        <div className="max-h-96 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase text-muted">
                <th className="py-2 pr-2">{t(I18nKey.CYBER_MONITOR$TIME)}</th>
                <th className="py-2 pr-2">
                  {t(I18nKey.CYBER_MONITOR$SEVERITY_CRITICAL)}
                </th>
                <th className="py-2 pr-2">{t(I18nKey.CYBER_MONITOR$VECTOR)}</th>
                <th className="py-2 pr-2">{t(I18nKey.CYBER_MONITOR$SOURCE)}</th>
                <th className="py-2">{t(I18nKey.CYBER_MONITOR$STATUS)}</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr
                  key={e.id}
                  data-testid="cyber-feed-row"
                  onClick={() => onSelect(e)}
                  className="cursor-pointer border-t border-border hover:bg-surface-raised"
                >
                  <td className="py-2 pr-2 text-muted">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-2 pr-2">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-xs ${SEVERITY_BADGE_CLASS[e.severity]}`}
                    >
                      {t(severityLabelKey(e.severity))}
                    </span>
                  </td>
                  <td className="py-2 pr-2 text-content">{e.vector}</td>
                  <td className="py-2 pr-2 text-content">
                    {e.sourceIp}
                    <span className="ml-2 text-xs text-muted">
                      {e.origin.city}, {e.origin.country}
                    </span>
                  </td>
                  <td className="py-2 text-muted">
                    {t(statusLabelKey(e.status))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
