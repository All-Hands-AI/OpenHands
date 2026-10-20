import React from "react";

const CyberMonitor = React.lazy(() =>
  import("#/components/features/cyber-monitor/cyber-monitor").then((m) => ({
    default: m.CyberMonitor,
  })),
);

export default function CyberMonitorRoute() {
  return (
    <React.Suspense fallback={null}>
      <CyberMonitor />
    </React.Suspense>
  );
}
