export * from "./lib";

// The library stylesheet. Vite library mode extracts these imports, plus the
// CSS that components import (such as xterm), into `dist/styles.css` and strips
// them from the emitted JavaScript, so hosts load that file explicitly with
// `import "@openhands/agent-canvas/styles.css"`. They come after the exports:
// placed first, the stripped imports leave a dangling comma at the start of
// `dist/index.cjs`, which then fails to parse.
import "./tailwind.css";
import "./index.css";
