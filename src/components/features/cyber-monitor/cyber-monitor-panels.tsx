import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import type { ThreatSeverity } from "./cyber-monitor-types";

export const SEVERITY_BADGE_CLASS: Record<ThreatSeverity, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  low: "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

export const SEVERITY_DOT_CLASS: Record<ThreatSeverity, string> = {
  critical: "bg-red-400",
  high: "bg-orange-400",
  medium: "bg-yellow-400",
  low: "bg-sky-400",
};

export function severityLabelKey(
  s: ThreatSeverity,
): (typeof I18nKey)[keyof typeof I18nKey] {
  switch (s) {
    case "critical":
      return I18nKey.CYBER_MONITOR$SEVERITY_CRITICAL;
    case "high":
      return I18nKey.CYBER_MONITOR$SEVERITY_HIGH;
    case "medium":
      return I18nKey.CYBER_MONITOR$SEVERITY_MEDIUM;
    case "low":
      return I18nKey.CYBER_MONITOR$SEVERITY_LOW;
  }
}

export function KpiCard({
  label,
  value,
  testId,
}: {
  label: string;
  value: string;
  testId: string;
}) {
  return (
    <div
      className="rounded-xl border border-border bg-surface p-4"
      data-testid={testId}
    >
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-content">{value}</p>
    </div>
  );
}

export function SeverityDonut({
  counts,
  total,
}: {
  counts: Record<ThreatSeverity, number>;
  total: number;
}) {
  const { t } = useTranslation("openhands");
  const order: ThreatSeverity[] = ["critical", "high", "medium", "low"];
  const colors: Record<ThreatSeverity, string> = {
    critical: "#f87171",
    high: "#fb923c",
    medium: "#facc15",
    low: "#38bdf8",
  };
  let acc = 0;
  const segments = order.map((s) => {
    const frac = total === 0 ? 0 : counts[s] / total;
    const seg = { s, start: acc, frac };
    acc += frac;
    return seg;
  });
  const gradient =
    total === 0
      ? "#334155"
      : segments
          .map(
            (seg) =>
              `${colors[seg.s]} ${seg.start * 360}deg ${(seg.start + seg.frac) * 360}deg`,
          )
          .join(", ");

  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="mb-3 text-sm font-semibold text-content">
        {t(I18nKey.CYBER_MONITOR$SEVERITY_DISTRIBUTION)}
      </h2>
      <div className="flex items-center gap-4">
        <div
          aria-hidden
          className="size-28 shrink-0 rounded-full"
          style={{
            background: `conic-gradient(${gradient})`,
            mask: "radial-gradient(circle, transparent 58%, black 59%)",
            WebkitMask: "radial-gradient(circle, transparent 58%, black 59%)",
          }}
        />
        <ul className="space-y-1 text-sm">
          {order.map((s) => (
            <li key={s} className="flex items-center gap-2 text-content">
              <span
                className={`size-2 rounded-full ${SEVERITY_DOT_CLASS[s]}`}
              />
              {t(severityLabelKey(s))}
              <span className="text-muted">{counts[s]}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function RankedList({
  title,
  rows,
  testId,
}: {
  title: string;
  rows: { label: string; sub?: string; count: number }[];
  testId: string;
}) {
  const max = Math.max(1, ...rows.map((r) => r.count));
  return (
    <section
      className="rounded-xl border border-border bg-surface p-4"
      data-testid={testId}
    >
      <h2 className="mb-3 text-sm font-semibold text-content">{title}</h2>
      <ul className="space-y-2">
        {rows.map((r) => (
          <li key={r.label}>
            <div className="flex justify-between text-sm">
              <span className="text-content">
                {r.label}
                {r.sub ? (
                  <span className="ml-2 text-xs text-muted">{r.sub}</span>
                ) : null}
              </span>
              <span className="text-muted">{r.count}</span>
            </div>
            <div className="mt-1 h-1.5 rounded bg-muted/20">
              <div
                className="h-1.5 rounded bg-red-400/80"
                style={{ width: `${(r.count / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
