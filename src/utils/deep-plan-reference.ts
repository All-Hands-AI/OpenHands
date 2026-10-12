/**
 * Reference-chain validator for Deep Planning (#17819).
 *
 * Documents in the chain cite upstream sections inline as `[Req 3.1]`,
 * `[DB 2.1]`, `[BE 4.2]`, `[FE 1.1]`. A chain is valid when every citation
 * resolves to a section that actually exists in an *upstream* document, and
 * every requirement is picked up by at least one task.
 *
 * Kept pure (no React, no store) so it can be unit-tested in both directions —
 * a validator that only ever returns `ok` would be indistinguishable from one
 * that is not running at all.
 */

import {
  DEEP_PLAN_LABEL_TO_PHASE,
  DEEP_PLAN_PHASE_IDS,
  DEEP_PLAN_PHASES,
  type DeepPlanLabel,
  type DeepPlanPhaseId,
  upstreamPhasesOf,
} from "#/utils/deep-plan";

export type RefIssueReason =
  /** The cited section does not exist in the upstream document. */
  | "dangling"
  /** The cited label belongs to a phase that is not upstream of this document. */
  | "not-upstream"
  /** The cited label has no document in the chain at all. */
  | "missing-document";

export interface RefIssue {
  /** Document the bad citation appears in. */
  from: DeepPlanPhaseId;
  /** The citation as written, e.g. `DB 2.5.1`. */
  ref: string;
  reason: RefIssueReason;
}

export interface RefReport {
  ok: boolean;
  issues: RefIssue[];
  /** Requirements sections no task cites. */
  uncovered: string[];
}

const REFERENCE_PATTERN = /\[(Req|DB|BE|FE)\s+([0-9]+(?:\.[0-9]+)*)\]/g;
const HEADING_PATTERN = /^#{1,6}\s+(.*)$/;
/**
 * An inline Markdown delimiter that may wrap a heading's leading section
 * number: bold (`**`/`__`), italic (`*`/`_`) or a code span (`` ` ``).
 */
const LEADING_MARKDOWN_WRAPPER = /^(\*\*|__|\*|_|`)/;
/**
 * A heading that leads with its section number, e.g. `## 3.1 Authentication`
 * defines `3.1`. Only a *leading* number counts, and it must be a standalone
 * number: a title like `## 3.1 Response under 200 ms` defines `3.1`, not
 * `200`, and `## Version 1.2` defines nothing.
 *
 * The number must not be glued to a following letter or digit — the packed
 * number already consumes every `.digit` group, so this rejects `## 3D Rendering`
 * and `## 3.1beta Authentication`, which are words rather than sections. It must
 * also not be continued by punctuation that keeps building a numeric
 * expression: `## 3,000 concurrent users` (a quantity) and `## 3-4 servers`
 * (a range) define nothing. The lookahead `(?:[,./-]?\d)` rejects a digit that
 * follows a numeric separator, and also blocks the engine from backtracking to
 * a shorter number and treating the dot of a larger one (`3.1beta` → `3`) as a
 * delimiter. Any real delimiter is fine: whitespace, the end of the heading, a
 * supported closing Markdown marker (`*`/`_`/`` ` ``, left by unwrapping a
 * wrapped number) or section separators such as `## 3.1: Authentication`,
 * `## 3.1) Authentication` and `## 3. Response`. Unicode-aware, so a non-ASCII
 * letter also blocks the number.
 */
const LEADING_NUMBER_HEADING =
  /^([0-9]+(?:\.[0-9]+)*)(?![\p{L}\p{N}]|[,./-]?\d)/u;
/**
 * A heading that spells its own label out at the start, e.g.
 * `## [Req 3.1] Users` — the citation *is* the section number here.
 */
const OWN_LABEL_HEADING = /^\[(?:Req|DB|BE|FE)\s+([0-9]+(?:\.[0-9]+)*)\]/;

export type DeepPlanDocuments = Partial<Record<DeepPlanPhaseId, string>>;

/**
 * The section number a heading defines, or `null` when it defines none.
 *
 * A heading leads with its number (`## 3.1 Authentication` defines `3.1`) or
 * spells its own label out (`## [Req 3.1] Authentication`). Only a *leading*
 * number counts, so prose numbers (`## 3.1 Response under 200 ms` → `3.1`, not
 * `200`) and version-like titles (`## Version 1.2` → nothing) are ignored.
 * Shared by {@link extractDefinedSections} and the document-chain renderer so
 * both agree on which sections exist.
 */
export function definedSectionOfHeading(rawTitle: string): string | null {
  const title = stripClosedWrapper(rawTitle.trimStart());
  const leadingNumber = LEADING_NUMBER_HEADING.exec(title);
  if (leadingNumber) return leadingNumber[1];
  const ownLabel = OWN_LABEL_HEADING.exec(title);
  if (ownLabel) return ownLabel[1];
  return null;
}

/** The section number a single line defines, or `null` when it is not a heading. */
export function sectionHeadingOfLine(line: string): string | null {
  const heading = HEADING_PATTERN.exec(line);
  if (!heading) return null;
  return definedSectionOfHeading(heading[1]);
}

/**
 * Strips leading inline Markdown delimiters so the leading-token check sees the
 * rendered heading. A delimiter is only a wrapper when it actually forms a span
 * under Markdown's closing rules: a code span closes at the next backtick, and
 * an emphasis marker closes only at a right-flanking run — one preceded by a
 * non-whitespace character — and at the *first* later run, since an inner span
 * binds first. This rejects a literal marker followed by separate emphasis,
 * e.g. `## *3.1 Authentication *notes*`, where the leading `*` cannot pair with
 * the `*` before `notes` and so stays visible. An unmatched marker
 * (`## *3.1 Authentication`) is likewise shown literally and not stripped.
 */
function stripClosedWrapper(title: string): string {
  let visible = title;
  for (;;) {
    const marker = LEADING_MARKDOWN_WRAPPER.exec(visible)?.[1];
    if (!marker) return visible;
    const rest = visible.slice(marker.length);
    const closesAt = rest.indexOf(marker);
    if (closesAt <= 0) return visible;
    // A code span ignores flanking; an emphasis closer must not be preceded by
    // whitespace.
    if (marker !== "`" && /\s/.test(rest[closesAt - 1])) return visible;
    visible = rest;
  }
}

/**
 * Section numbers a document defines, taken from its numbered headings
 * (`## 3.1 Authentication` defines `3.1`; `### 3.1.1 Login` defines `3.1.1`).
 * Only a number that *leads* the heading is a definition, so prose numbers in
 * a title (`## 3.1 Response under 200 ms` → `3.1`, not `200`) and version-like
 * titles (`## Version 1.2` → nothing) are ignored. A supported inline Markdown
 * wrapper — around the number (`## **3.1** Authentication`) or the whole title
 * (`## **3.1 Authentication**`) — does not hide it, since the rendered heading
 * still starts with the number; an unmatched marker stays literal and defines
 * nothing.
 *
 * A heading may instead spell its own label out (`## [Req 3.1] Authentication`),
 * in which case the leading citation is the definition. An unnumbered heading
 * that merely cites upstream (`## Users [Req 3.1]`) defines nothing — counting
 * it would let a downstream `[DB 3.1]` resolve against a section this document
 * never defines.
 */
export function extractDefinedSections(content: string): Set<string> {
  const sections = new Set<string>();
  for (const line of content.split("\n")) {
    const section = sectionHeadingOfLine(line);
    if (section !== null) sections.add(section);
  }
  return sections;
}

/** Every citation in a document, in order of appearance. */
export function extractReferences(
  content: string,
): { label: DeepPlanLabel; section: string }[] {
  const refs: { label: DeepPlanLabel; section: string }[] = [];
  for (const match of content.matchAll(REFERENCE_PATTERN)) {
    refs.push({ label: match[1] as DeepPlanLabel, section: match[2] });
  }
  return refs;
}

/**
 * Custom URL scheme for citation links. A scheme (rather than an in-page `#`
 * fragment) keeps a citation from resolving against the host page's own URL;
 * the renderer's anchor handler intercepts it and scrolls to the cited
 * document in the chain.
 */
export const DEEP_PLAN_CITATION_SCHEME = "deep-plan-doc:";

/** DOM id of a document's wrapper in the chain. */
export const deepPlanDocumentId = (phase: DeepPlanPhaseId): string =>
  `deep-plan-document-${phase}`;

/** DOM id of a cited section heading within a phase document. */
export const deepPlanSectionId = (
  phase: DeepPlanPhaseId,
  section: string,
): string => `deep-plan-section-${phase}-${section}`;

/** The `deep-plan-doc:<phase>#<section>` href a citation link carries. */
export const deepPlanCitationHref = (
  phase: DeepPlanPhaseId,
  section: string,
): string => `${DEEP_PLAN_CITATION_SCHEME}${phase}#${section}`;

/** Parse a citation href back to its target; `null` when it is not one. */
export function parseDeepPlanCitation(
  href: string | undefined,
): { phase: DeepPlanPhaseId; section: string } | null {
  if (!href?.startsWith(DEEP_PLAN_CITATION_SCHEME)) return null;
  const rest = href.slice(DEEP_PLAN_CITATION_SCHEME.length);
  const hash = rest.indexOf("#");
  const phase = (hash === -1 ? rest : rest.slice(0, hash)) as DeepPlanPhaseId;
  if (!DEEP_PLAN_PHASE_IDS.includes(phase)) return null;
  return { phase, section: hash === -1 ? "" : rest.slice(hash + 1) };
}

/**
 * Rewrites every real citation in `content` into a Markdown link that targets
 * the document and section that owns the cited label. A citation the validator
 * would reject (`not-upstream`, or the document's own label, which is a
 * self-definition rather than a dependency) is left untouched, so the chain
 * only offers links the checkpoint agrees are valid.
 */
export function linkifyCitations(
  content: string,
  from: DeepPlanPhaseId,
): string {
  const upstream = new Set(upstreamPhasesOf(from));
  return content.replace(
    REFERENCE_PATTERN,
    (match, label: DeepPlanLabel, section: string) => {
      const target = DEEP_PLAN_LABEL_TO_PHASE[label];
      if (target === from) return match;
      if (!upstream.has(target)) return match;
      return `[${match}](${deepPlanCitationHref(target, section)})`;
    },
  );
}

export function validateDocumentChain(
  documents: DeepPlanDocuments,
  /**
   * Only validate documents up to and including this phase. A checkpoint
   * validates the document it is confirming; later documents are validated at
   * their own checkpoints. Validating the whole chain here would let a stale
   * citation in a document the user has not reached block an upstream
   * reconfirmation they have no way to repair from that checkpoint.
   */
  throughPhase?: DeepPlanPhaseId,
): RefReport {
  const issues: RefIssue[] = [];
  const sectionsByPhase = new Map<DeepPlanPhaseId, Set<string>>();

  const lastIndex = throughPhase
    ? DEEP_PLAN_PHASE_IDS.indexOf(throughPhase)
    : DEEP_PLAN_PHASE_IDS.length - 1;

  for (const phase of DEEP_PLAN_PHASES) {
    const content = documents[phase.id];
    if (content !== undefined) {
      sectionsByPhase.set(phase.id, extractDefinedSections(content));
    }
  }

  for (const phase of DEEP_PLAN_PHASES) {
    const content = documents[phase.id];
    if (content === undefined) continue;
    if (DEEP_PLAN_PHASE_IDS.indexOf(phase.id) > lastIndex) continue;

    const upstream = new Set(upstreamPhasesOf(phase.id));

    for (const { label, section } of extractReferences(content)) {
      const ref = `${label} ${section}`;
      const target = DEEP_PLAN_LABEL_TO_PHASE[label];

      // A document citing its own label is spelling out a section it defines
      // (`### 3.1 Create Endpoint [Req 3.1]`, `## [Req 3.1] Users`), not
      // depending on an upstream phase. `extractDefinedSections` already takes
      // the definition from that same heading, so validating the label again
      // would only re-derive it — and, because requirements has no upstream at
      // all, every self-label would otherwise read as `not-upstream` and block
      // the checkpoint meant to confirm the very sections it names.
      if (target === phase.id) continue;

      if (!upstream.has(target)) {
        issues.push({ from: phase.id, ref, reason: "not-upstream" });
        continue;
      }

      const defined = sectionsByPhase.get(target);
      if (!defined) {
        issues.push({ from: phase.id, ref, reason: "missing-document" });
        continue;
      }

      if (!defined.has(section)) {
        issues.push({ from: phase.id, ref, reason: "dangling" });
      }
    }
  }

  // Requirements coverage: every requirement section must be cited by a task.
  // Only meaningful once the tasks document is inside the validated range;
  // before that, "uncovered" would flag requirements the user simply has not
  // written tasks for yet.
  const uncovered: string[] = [];
  const requirementSections = sectionsByPhase.get("requirements");
  const tasks = documents.tasks;
  const tasksInRange = DEEP_PLAN_PHASE_IDS.indexOf("tasks") <= lastIndex;
  if (requirementSections && tasks !== undefined && tasksInRange) {
    const citedByTasks = new Set(
      extractReferences(tasks)
        .filter((ref) => ref.label === "Req")
        .map((ref) => ref.section),
    );
    for (const section of requirementSections) {
      if (!citedByTasks.has(section)) uncovered.push(section);
    }
    uncovered.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  }

  return { ok: issues.length === 0, issues, uncovered };
}
