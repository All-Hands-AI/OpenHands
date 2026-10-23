import { test, expect } from "file:///Users/enyst/.codex/worktrees/repair-main-ci/odie/node_modules/%40playwright/test/index.mjs";
import { existsSync } from 'node:fs';
test.describe.configure({ mode: 'serial' });
test('first case passes', () => {});
test('transient failure passes on retry', ({}, info) => expect(info.retry).toBe(1));
test('completion marker stays absent until final retry finishes', () => {
  expect(existsSync('.mock-llm-markers/.tests-done')).toBe(false);
});
