import React from "react";
import { useHandleRuntimeActive } from "./hooks/use-handle-runtime-active";
import useStreamUseCaseForUser from "./hooks/use-stream-usecase";

export function ShareEventHandler({
  conversationId,
  children,
}: React.PropsWithChildren<{ conversationId: string }>) {
  useStreamUseCaseForUser(conversationId);
  useHandleRuntimeActive();

  return children;
}
