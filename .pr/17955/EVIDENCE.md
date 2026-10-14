# Retained verification evidence

This evidence comes from the stopped `settings-17955-after-20261013` run at
fix revision `13da51daff35ae685f8fe13d3723b69c8464ab76`.

It covers only `F10.create-prefill`: the displayed inherited temperature `0.4`
survives creation and reopening of a new LLM profile, on desktop and phone,
two attempts each. The four attempts are recorded as **xpass**; each report
contains the asserted value before and after saving. These are fix-side results,
not a complete baseline/fix proof or verification of every profile option.

`evidence/` retains 22 files: eight screenshots, eight MP4/GIF recordings,
four assertion reports and two ledgers. Some captures repeat the same state;
the count is files, not independent checks. Raw stdout/stderr, embedded recipe
scripts and machine-local paths were removed from committed reports; original
private transcripts remain outside Git. Media received credential-pattern OCR
screening across the stills and sampled recording frames. No private runtime
state, credentials or traces are committed.

The feature-map update adds the reproducible desktop/phone known-bug recipes.
The design page describes the source proposal and does not substitute for live
proof. Issue #17955 remains open; this local fix has not been merged upstream.
