import React from "react";
import { createRoot } from "react-dom/client";
import { AgentServerUIProviders } from "@openhands/agent-canvas";
import "@openhands/agent-canvas/styles.css";
const h = React.createElement;
function App() {
  const [count, setCount] = React.useState(0);
  return h(AgentServerUIProviders, { analytics: false, styleOverrides: { "--oh-color-base": "#101820" } },
    h("div", { id: "probe", className: "flex flex-col gap-4 p-6 bg-canvas-base text-foreground rounded-xl" },
      h("span", { id: "a" }, "Probe A (flex column, gap-4, p-6, bg-canvas-base)"),
      h("span", { id: "b" }, "Probe B"),
      h("button", { id: "inside", className: "px-4 py-2 rounded-md bg-primary text-on-primary", onClick: () => setCount((v) => v + 1) }, "Inside Canvas " + count)));
}
createRoot(document.getElementById("root")).render(h(App));
