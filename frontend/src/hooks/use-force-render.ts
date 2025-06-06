import React from "react";

// Custom hook to force a component to re-render.
// This can be useful in scenarios where you need to trigger a re-render
// without changing the state or props of the component.
export function useForceRender() {
  const [, forceRender] = React.useReducer((x) => x + 1, 0);

  return forceRender;
}
