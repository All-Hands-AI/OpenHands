// Renders the output of scripts/check-sdk-version-sync.mjs into version-sync.svg.
// Run from the repo root: node .pr/bump-sdk-automation-1.57.0/make-evidence.mjs
import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const result = spawnSync("node", ["scripts/check-sdk-version-sync.mjs"], {
  encoding: "utf8",
});
const output = `${result.stdout}${result.stderr}`.replace(/\x1b\[[0-9;]*m/g, "");
const lines = [
  "$ node scripts/check-sdk-version-sync.mjs",
  ...output.split("\n").filter((line) => line.trim() !== ""),
  `exit code: ${result.status}`,
];

const escape = (text) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const lineHeight = 20;
const height = lines.length * lineHeight + 30;
const text = lines
  .map((line, i) => {
    const colour = /✗|mismatch/i.test(line)
      ? "#f85149"
      : /✓|in sync|exit code: 0/.test(line)
        ? "#3fb950"
        : "#e6edf3";
    return `<text x="16" y="${28 + i * lineHeight}" fill="${colour}">${escape(line)}</text>`;
  })
  .join("\n  ");

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="${height}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="14">
  <rect width="100%" height="100%" rx="8" fill="#0d1117"/>
  ${text}
</svg>
`;
const out = join(dirname(fileURLToPath(import.meta.url)), "version-sync.svg");
writeFileSync(out, svg);
console.log(`wrote ${out} (check exit code ${result.status})`);
