import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import {
  CYBER_MONITOR_TARGET,
  THREAT_ORIGINS,
  type ThreatEvent,
} from "./cyber-monitor-types";

const MAP_WIDTH = 800;
const MAP_HEIGHT = 360;

function project(lat: number, lon: number): { x: number; y: number } {
  return {
    x: ((lon + 180) / 360) * MAP_WIDTH,
    y: ((90 - lat) / 180) * MAP_HEIGHT,
  };
}

const DOTS: { x: number; y: number }[] = [];
for (let lon = -170; lon <= 170; lon += 10) {
  for (let lat = -60; lat <= 75; lat += 10) {
    const jitter = ((lon * 7 + lat * 13) % 5) - 2;
    DOTS.push(project(lat + jitter, lon));
  }
}

const SEVERITY_FILL: Record<ThreatEvent["severity"], string> = {
  critical: "#f87171",
  high: "#fb923c",
  medium: "#facc15",
  low: "#38bdf8",
};

export function CyberAttackMap({ events }: { events: ThreatEvent[] }) {
  const { t } = useTranslation("openhands");
  const target = project(CYBER_MONITOR_TARGET.lat, CYBER_MONITOR_TARGET.lon);
  const recent = events.slice(0, 14);

  return (
    <section
      aria-label={t(I18nKey.CYBER_MONITOR$MAP_LABEL)}
      className="rounded-xl border border-border bg-surface p-4"
    >
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-content">
          {t(I18nKey.CYBER_MONITOR$MAP_LABEL)}
        </h2>
        <span className="text-xs text-muted">
          {t(I18nKey.CYBER_MONITOR$TARGET_LABEL)}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
        className="w-full"
        role="img"
        aria-label={t(I18nKey.CYBER_MONITOR$MAP_LABEL)}
      >
        {DOTS.map((d, i) => (
          <circle key={i} cx={d.x} cy={d.y} r={1.6} className="fill-muted/40" />
        ))}
        {recent.map((e) => {
          const from = project(e.origin.lat, e.origin.lon);
          const midX = (from.x + target.x) / 2;
          const midY = Math.min(from.y, target.y) - 60;
          const color = SEVERITY_FILL[e.severity];
          return (
            <g key={e.id}>
              <path
                d={`M ${from.x} ${from.y} Q ${midX} ${midY} ${target.x} ${target.y}`}
                fill="none"
                stroke={color}
                strokeWidth={1.6}
                strokeDasharray="6 4"
                opacity={0.85}
              >
                <animate
                  attributeName="stroke-dashoffset"
                  from="20"
                  to="0"
                  dur="1.2s"
                  repeatCount="indefinite"
                />
              </path>
              <circle cx={from.x} cy={from.y} r={4} fill={color} />
              <circle cx={target.x} cy={target.y} r={5} fill={color}>
                <animate
                  attributeName="r"
                  values="4;14;4"
                  dur="2s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values="0.9;0.15;0.9"
                  dur="2s"
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          );
        })}
        {THREAT_ORIGINS.map((o) => {
          const p = project(o.lat, o.lon);
          return (
            <text
              key={o.countryCode}
              x={p.x + 8}
              y={p.y - 6}
              fontSize={11}
              className="fill-content"
            >
              {o.city}
            </text>
          );
        })}
        <circle
          cx={target.x}
          cy={target.y}
          r={5}
          className="fill-emerald-400"
        />
        <text
          x={target.x + 9}
          y={target.y + 4}
          fontSize={12}
          className="fill-content font-semibold"
        >
          {CYBER_MONITOR_TARGET.city}
        </text>
      </svg>
    </section>
  );
}
