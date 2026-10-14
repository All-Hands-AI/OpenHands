# Verification evidence — #18432

**Bug:** the agent's "needs a secret" dialog is a fixed 520 px wide, so on a
390 px phone it overflows the viewport and its title/fields/buttons are cut off.

**Fix:** `ModalBody` now applies `MODAL_MAX_WIDTH_VIEWPORT` (`max-w-[90vw]`),
the same cap the hand-capped dialogs add themselves. The constant already
existed in `modal-body.tsx`; `ModalBody` was the one render path that never
applied it.

## 1. Unit tests

```
npx vitest run src/components/shared/modals/modal-body.test.tsx
→ Test Files 1 passed (1) | Tests 3 passed (3)
```

The same test file fails on `main` (verified by stashing the fix: 3 failed).

## 2. Layout measurement with the real compiled CSS

Widths measured in a real browser (Chrome, dev server) at 390×844 and
1440×1000, using the exact class strings `ModalBody` renders and the real
`ModalBackdrop` structure (`fixed inset-0 flex items-center justify-center` →
`div.relative` → body):

| viewport | before the fix | after the fix |
| --- | --- | --- |
| 390×844 | `x=-65, width=520` — overflows, **inside=false** | `x=20, width=351` — **inside=true** |
| 1440×1000 | `x=460, width=520` — inside=true | `x=460, width=520` — inside=true |

The "before" numbers reproduce the values reported in the issue
(`{"x": -65, "width": 520}, insideViewport: false`), and the expected phone
width in the issue's acceptance criteria ("at most 90vw wide — 351 px at
390 px").

Screenshots: `phone-before.png` (cut off on both edges) and
`phone-after.png` (fits, 351 px).

## 3. Not covered here

The dialog was not triggered end-to-end through a running agent (that needs a
full agent-server stack). Reviewers can re-run the issue's `control-openhands`
reproduction on a mock-LLM stack to confirm the same numbers on the real
dialog.
