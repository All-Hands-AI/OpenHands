import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import type { ConsoleEntry } from "./cyber-monitor-types";

function consoleText(
  e: ConsoleEntry,
  t: ReturnType<typeof useTranslation<"openhands">>["t"],
): string {
  switch (e.messageKey) {
    case "started":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_STARTED);
    case "blocked":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_BLOCKED, {
        vector: e.vector ?? "",
        ip: e.ip ?? "",
      });
    case "surge":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_SURGE);
    case "paused":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_PAUSED);
    case "resumed":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_RESUMED);
    case "ip_blocked":
      return t(I18nKey.CYBER_MONITOR$CONSOLE_IP_BLOCKED, { ip: e.ip ?? "" });
  }
}

const KIND_CLASS: Record<ConsoleEntry["kind"], string> = {
  info: "text-sky-400",
  warn: "text-yellow-400",
  block: "text-red-400",
  surge: "text-orange-400",
};

export function CyberSocConsole({ entries }: { entries: ConsoleEntry[] }) {
  const { t } = useTranslation("openhands");
  return (
    <section className="rounded-xl border border-border bg-black/40 p-4">
      <h2 className="mb-3 text-sm font-semibold text-content">
        {t(I18nKey.CYBER_MONITOR$SOC_CONSOLE)}
      </h2>
      <ul
        data-testid="cyber-console"
        className="max-h-56 space-y-1 overflow-auto font-mono text-xs"
      >
        {entries.map((e) => (
          <li key={e.id} className={KIND_CLASS[e.kind]}>
            <span className="text-muted">
              {new Date(e.timestamp).toLocaleTimeString()}{" "}
            </span>
            {consoleText(e, t)}
          </li>
        ))}
      </ul>
    </section>
  );
}
