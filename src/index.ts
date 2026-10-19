// The library stylesheet. Vite library mode extracts these imports, plus the
// CSS that components import (such as xterm), into `dist/styles.css` and strips
// them from the emitted JavaScript, so hosts load that file explicitly with
// `import "@openhands/agent-canvas/styles.css"`.
import "./tailwind.css";
import "./index.css";

export * from "./lib";
