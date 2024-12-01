import React from "react";
import { useWSStatusChange } from "./hooks/use-ws-status-change";
import { useHandleWSEvents } from "./hooks/use-handle-ws-events";
import { useHandleRuntimeActive } from "./hooks/use-handle-runtime-active";

export function EventHandler({ children }: React.PropsWithChildren) {
  useWSStatusChange();
  useHandleWSEvents();
  useHandleRuntimeActive();

  return children;
}
