import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import type { ThreatEvent } from "./cyber-monitor-types";
import { SEVERITY_BADGE_CLASS, severityLabelKey } from "./cyber-monitor-panels";
import { statusLabelKey } from "./cyber-threat-feed";

export function CyberThreatDrawer({
  threat,
  isBlocked,
  onClose,
  onBlockIp,
}: {
  threat: ThreatEvent;
  isBlocked: boolean;
  onClose: () => void;
  onBlockIp: (ip: string) => void;
}) {
  const { t } = useTranslation("openhands");
  const rows: { label: string; value: string }[] = [
    {
      label: t(I18nKey.CYBER_MONITOR$SOURCE),
      value: `${threat.sourceIp} (${threat.origin.asn})`,
    },
    { label: t(I18nKey.CYBER_MONITOR$VECTOR), value: threat.vector },
    {
      label: t(I18nKey.CYBER_MONITOR$TARGET_LABEL),
      value: threat.targetAsset,
    },
    { label: t(I18nKey.CYBER_MONITOR$PORT), value: String(threat.port) },
    {
      label: t(I18nKey.CYBER_MONITOR$PAYLOAD),
      value: `${threat.payloadKb} KB`,
    },
    {
      label: t(I18nKey.CYBER_MONITOR$STATUS),
      value: t(statusLabelKey(threat.status)),
    },
    {
      label: t(I18nKey.CYBER_MONITOR$TIME),
      value: new Date(threat.timestamp).toLocaleString(),
    },
  ];
  return (
    <aside
      data-testid="cyber-threat-drawer"
      className="fixed inset-y-0 right-0 z-50 w-full max-w-sm border-l border-border bg-surface p-5 shadow-xl"
      aria-label={t(I18nKey.CYBER_MONITOR$THREAT_DETAIL)}
    >
      <div className="mb-4 flex items-start justify-between">
        <h2 className="text-base font-semibold text-content">
          {t(I18nKey.CYBER_MONITOR$THREAT_DETAIL)}
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label={t(I18nKey.CYBER_MONITOR$CLOSE)}
          className="rounded-md border border-border px-2 py-1 text-sm text-content"
        >
          {t(I18nKey.CYBER_MONITOR$CLOSE)}
        </button>
      </div>
      <span
        className={`rounded-full border px-2 py-0.5 text-xs ${SEVERITY_BADGE_CLASS[threat.severity]}`}
      >
        {t(severityLabelKey(threat.severity))}
      </span>
      <p className="mt-3 text-sm text-muted">
        {threat.origin.city}, {threat.origin.country}
      </p>
      <dl className="mt-4 space-y-3">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between gap-4 text-sm">
            <dt className="text-muted">{r.label}</dt>
            <dd className="text-right text-content">{r.value}</dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        data-testid="cyber-block-ip"
        disabled={isBlocked}
        onClick={() => onBlockIp(threat.sourceIp)}
        className="mt-6 w-full rounded-md bg-red-500/90 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isBlocked
          ? t(I18nKey.CYBER_MONITOR$IP_BLOCKED)
          : t(I18nKey.CYBER_MONITOR$BLOCK_IP)}
      </button>
    </aside>
  );
}
