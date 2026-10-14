import type { TFunction } from "i18next";
import { describe, expect, it } from "vitest";
import { I18nKey } from "#/i18n/declaration";
import {
  extractDefinedSections,
  extractReferences,
  linkifyCitations,
  parseDeepPlanCitation,
  validateDocumentChain,
  type DeepPlanDocuments,
} from "#/utils/deep-plan-reference";
import { makeRefIssueMessage } from "#/utils/deep-plan-messages";

const requirements = [
  "# Requirements",
  "",
  "## 1 Scope",
  "",
  "## 3.1 Authentication",
  "",
  "### 3.1.1 Login",
  "",
  "## 5.1 Reporting",
].join("\n");

const database = [
  "# Database design",
  "",
  "## 2.1 Users [Req 3.1]",
  "",
  "### 2.5.1 Sessions [Req 3.1.1]",
].join("\n");

const validChain = (): DeepPlanDocuments => ({
  requirements,
  database,
  backend: [
    "# Backend design",
    "",
    "## 4.2 Login endpoint [Req 3.1] [DB 2.5.1]",
  ].join("\n"),
  frontend: [
    "# Frontend design",
    "",
    "## 1.1 Login form [Req 3.1] [DB 2.1] [BE 4.2]",
  ].join("\n"),
  tasks: [
    "# Tasks",
    "",
    "- [ ] T1 Login [Req 3.1] [DB 2.1] [BE 4.2] [FE 1.1]",
    "- [ ] T2 Sessions [Req 3.1.1]",
    "- [ ] T3 Reporting [Req 5.1]",
    "- [ ] T4 Scope [Req 1]",
  ].join("\n"),
});

describe("extractDefinedSections", () => {
  it("collects the numbered headings a document defines", () => {
    expect([...extractDefinedSections(requirements)].sort()).toEqual([
      "1",
      "3.1",
      "3.1.1",
      "5.1",
    ]);
  });

  it("ignores body text that is not a heading", () => {
    expect([...extractDefinedSections("See 9.9 for details.")]).toEqual([]);
  });

  it("does not count a heading's upstream citation as a defined section", () => {
    // `## 2.1 Users [Req 3.1]` defines 2.1 only. Counting 3.1 as well would let
    // a downstream `[DB 3.1]` resolve against a section the database document
    // never defines, defeating the whole traceability guarantee.
    expect([...extractDefinedSections("## 2.1 Users [Req 3.1]")]).toEqual([
      "2.1",
    ]);
  });

  it("still reads a section from a heading that spells its own label out", () => {
    expect([...extractDefinedSections("## [Req 3.1] Users")]).toEqual(["3.1"]);
  });

  it("reads a section from a heading that leads with the document's own label", () => {
    // The live planner writes requirement headings as `### Req 1.1 — …`. Without
    // recognizing the leading label the number is invisible, so a downstream
    // `[Req 1.1]` is wrongly rejected as dangling.
    expect([
      ...extractDefinedSections(
        "### Req 1.1 — Resource exposure",
        "requirements",
      ),
    ]).toEqual(["1.1"]);
    expect([
      ...extractDefinedSections("## DB 2.1 Todos table", "database"),
    ]).toEqual(["2.1"]);
    // The label must be a whole word, and the number keeps its trailing guard.
    expect([
      ...extractDefinedSections("## Requisite 1.1", "requirements"),
    ]).toEqual([]);
    expect([
      ...extractDefinedSections("## Req 1.1beta", "requirements"),
    ]).toEqual([]);
    expect([...extractDefinedSections("## Req 1.12", "requirements")]).toEqual([
      "1.12",
    ]);
  });

  it("does not register an upstream label as one of the document's own", () => {
    // A database document may organize itself around the requirements it
    // satisfies (`## Req 3.1 …`), but those headings define *requirement*
    // sections, not DB ones. Counting them under the database phase would let a
    // downstream `[DB 3.1]` resolve against a section the database never
    // defines — the traceability hole this validator exists to close.
    const database = [
      "# Database design",
      "## Req 3.1 Resource exposure",
      "## DB 2.1 todos table",
    ].join("\n");
    expect([...extractDefinedSections(database, "database")].sort()).toEqual([
      "2.1",
    ]);
    // Without an owning phase the ambiguous label-leading form defines nothing.
    expect([...extractDefinedSections("## Req 1.1 Resource exposure")]).toEqual(
      [],
    );
  });

  it("only counts a heading's leading number, not prose numbers in the title", () => {
    // `200` is an SLA figure, not a section the document defines; counting it
    // would let `[Req 200]` resolve against a section that never exists.
    expect([...extractDefinedSections("## 3.1 Response under 200 ms")]).toEqual(
      ["3.1"],
    );
  });

  it("defines nothing for a heading that does not lead with a number", () => {
    expect([...extractDefinedSections("## Version 1.2")]).toEqual([]);
  });

  it("does not treat a number that is part of a word as a section", () => {
    // `3D` and `3.1beta` are words, not section numbers; registering them would
    // let a downstream `[Req 3]` resolve against a section that never exists.
    expect([...extractDefinedSections("## 3D Rendering")]).toEqual([]);
    expect([...extractDefinedSections("## 3.1beta Authentication")]).toEqual(
      [],
    );
    expect([...extractDefinedSections("## 3.1.2Detail")]).toEqual([]);
    // A delimiter after the number still defines it.
    expect([...extractDefinedSections("## 3. Response")]).toEqual(["3"]);
    expect([...extractDefinedSections("## 3.1")]).toEqual(["3.1"]);
  });

  it("sees a number separated from its title by punctuation", () => {
    // `3.1: Authentication` is still a section 3.1 heading; rejecting it would
    // make a downstream `[Req 3.1]` dangling.
    expect([...extractDefinedSections("## 3.1: Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## 3.1) Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## 3.1. Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## 3) Authentication")]).toEqual(["3"]);
    // A separator may abut the title (`3.1:Auth` still defines `3.1`), but a
    // number glued directly to a letter does not.
    expect([...extractDefinedSections("## 3.1:Auth")]).toEqual(["3.1"]);
    expect([...extractDefinedSections("## 3.1Auth")]).toEqual([]);
  });

  it("does not read a numeric quantity or range as a section", () => {
    // `3,000` and `3-4` are numbers in a title, not section numbers with a
    // delimiter; registering them would let `[Req 3]` resolve against a section
    // the document never defines.
    expect([...extractDefinedSections("## 3,000 concurrent users")]).toEqual(
      [],
    );
    expect([...extractDefinedSections("## 3-4 servers")]).toEqual([]);
    expect([...extractDefinedSections("## 3/4 of capacity")]).toEqual([]);
    // A separator that ends the number still defines it.
    expect([...extractDefinedSections("## 3.1, Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## 3 - Authentication")]).toEqual(["3"]);
  });

  it("sees a leading number wrapped in supported inline Markdown", () => {
    // Markdown renders these wrappers without changing the displayed section
    // number, so a citation of the visible `3.1` must still resolve.
    expect([...extractDefinedSections("## **3.1** Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## `3.1` Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## *3.1* Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## _3.1_ Authentication")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("### *3.1.1* Login")]).toEqual(["3.1.1"]);
  });

  it("sees a leading number when a wrapper spans the whole title", () => {
    // The closing delimiter follows the title, not the number; the rendered
    // heading still starts with `3.1`.
    expect([...extractDefinedSections("## **3.1 Authentication**")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## *3.1 Authentication*")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## `3.1 Authentication`")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## __3.1 Authentication__")]).toEqual([
      "3.1",
    ]);
    expect([...extractDefinedSections("## _3.1 Authentication_")]).toEqual([
      "3.1",
    ]);
  });

  it("does not treat a wrapped prose number as a definition", () => {
    // Wrapping does not lift the leading-token constraint: `**200**` is still
    // prose, not a section.
    expect([
      ...extractDefinedSections("## 3.1 Response under **200** ms"),
    ]).toEqual(["3.1"]);
  });

  it("ignores an unmatched Markdown marker before the number", () => {
    // An unclosed delimiter renders literally, so the displayed heading does
    // not start with the number and defines no section.
    expect([...extractDefinedSections("## *3.1 Authentication")]).toEqual([]);
    expect([...extractDefinedSections("## `3.1 Authentication")]).toEqual([]);
    expect([...extractDefinedSections("## **3.1 Authentication")]).toEqual([]);
    // `*3.1*` closes, so it is a real definition even with a trailing marker.
    expect([...extractDefinedSections("## *3.1* Authentication")]).toEqual([
      "3.1",
    ]);
  });

  it("ignores a leading marker closed only by a separate emphasis span", () => {
    // The leading `*` cannot pair with the `*` before `notes` (they are not a
    // single span), so it stays literal and the heading starts with `*`, not
    // the number.
    expect([
      ...extractDefinedSections("## *3.1 Authentication *notes*"),
    ]).toEqual([]);
    // Same shape with the leading `*` separated from the number by whitespace.
    expect([...extractDefinedSections("## * 3.1 *notes*")]).toEqual([]);
  });

  it("does not define a section from an unnumbered heading's citation", () => {
    // `## Users [Req 3.1]` has no number of its own, so it defines nothing.
    // Treating the citation as a definition would let a downstream
    // `[DB 3.1]` resolve against a database section that never exists.
    expect([...extractDefinedSections("## Users [Req 3.1]")]).toEqual([]);
  });
});

describe("extractReferences", () => {
  it("reads every labelled citation in order", () => {
    expect(extractReferences("[Req 3.1] then [DB 2.5.1]")).toEqual([
      { label: "Req", section: "3.1" },
      { label: "DB", section: "2.5.1" },
    ]);
  });

  it("ignores labels outside the fixed vocabulary", () => {
    expect(extractReferences("[XX 1.1] [Req 3.1]")).toEqual([
      { label: "Req", section: "3.1" },
    ]);
  });

  it("ignores citations written inside inline code", () => {
    expect(extractReferences("Use `[Req 9.9]` as the example marker")).toEqual(
      [],
    );
  });

  it("ignores citations written inside fenced code", () => {
    expect(
      extractReferences(
        ["```", "[Req 9.9]", "```", "See [Req 3.1]"].join("\n"),
      ),
    ).toEqual([{ label: "Req", section: "3.1" }]);
  });

  it("ignores citations written inside an existing link", () => {
    expect(
      extractReferences("See [the requirement [Req 9.9]](https://example.com)"),
    ).toEqual([]);
  });

  it("counts a link whose whole label is a citation", () => {
    // A direct `[Req 9.9](url)` link names a section the chain must check; the
    // link being authored markup does not make the label illustrative.
    expect(extractReferences("[Req 9.9](https://example.com)")).toEqual([
      { label: "Req", section: "9.9" },
    ]);
  });

  it("ignores an image whose alt text looks like a citation", () => {
    // Image syntax shares the bracket-and-parenthesis shape of a link, but the
    // bracketed text is alt text, not a reference.
    expect(
      extractReferences("![Req 9.9](https://example.com/error.png)"),
    ).toEqual([]);
  });

  it("ignores an escaped link that renders literally", () => {
    expect(extractReferences("\\[Req 9.9](https://example.com)")).toEqual([]);
  });

  it("still counts a prose citation immediately after an image", () => {
    // The image is consumed whole, so a following prose citation is not lost.
    expect(
      extractReferences("![alt](https://example.com/a.png) see [Req 3.1]"),
    ).toEqual([{ label: "Req", section: "3.1" }]);
  });

  it("counts a link whose leading exclamation mark is escaped", () => {
    // `\!` renders a literal `!`, so the link that follows is real.
    expect(extractReferences("\\![Req 9.9](https://example.com)")).toEqual([
      { label: "Req", section: "9.9" },
    ]);
  });

  it("ignores an image behind an even backslash run", () => {
    // `\\!` renders a backslash then image syntax, so the alt text is not a
    // citation. An odd count would escape the `!` and make the link real.
    expect(extractReferences("\\\\![Req 9.9](https://example.com)")).toEqual(
      [],
    );
  });

  it("counts a link behind an even backslash run", () => {
    // `\\[` renders a backslash then a real link; only an odd count escapes it.
    expect(extractReferences("\\\\[Req 9.9](https://example.com)")).toEqual([
      { label: "Req", section: "9.9" },
    ]);
  });
});

describe("validateDocumentChain", () => {
  it("accepts a chain whose every citation resolves upstream", () => {
    const report = validateDocumentChain(validChain());

    expect(report.issues).toEqual([]);
    expect(report.ok).toBe(true);
    expect(report.uncovered).toEqual([]);
  });

  it("rejects a dangling reference to a section that does not exist upstream", () => {
    const documents = validChain();
    documents.backend = "## 4.2 Login endpoint [Req 3.1] [DB 2.5.1] [DB 9.9.9]";

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "backend", ref: "DB 9.9.9", reason: "dangling" },
    ]);
  });

  it("rejects a reference to a phase that is not upstream", () => {
    const documents = validChain();
    // The database design must not depend on the backend design. Drop the
    // downstream citations so this case isolates exactly one violation.
    documents.database = "## 2.1 Users [Req 3.1] [BE 4.2]";
    documents.backend = "# Backend design";
    documents.frontend = "# Frontend design";
    documents.tasks = "# Tasks";

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "BE 4.2", reason: "not-upstream" },
    ]);
  });

  it("accepts a document that spells out its own label to define a section", () => {
    // Live planners write `### 3.1 Create Endpoint [Req 3.1]`, annotating each
    // section with the label downstream phases cite. Requirements has no
    // upstream phase, so treating that self-label as a dependency would mark
    // every section `not-upstream` and block the checkpoint that confirms the
    // very document the planner just produced.
    const documents: DeepPlanDocuments = {
      requirements: [
        "# Requirements",
        "",
        "### 3.1 Create Endpoint [Req 3.1]",
        "",
        "### 3.2 Redirect Endpoint [Req 3.2]",
      ].join("\n"),
    };

    const report = validateDocumentChain(documents, "requirements");

    expect(report.ok).toBe(true);
    expect(report.issues).toEqual([]);
  });

  it("still reports a downstream citation to a document that cites only itself", () => {
    // A self-label is not an upstream definition: the database design cannot
    // resolve `[Req 3.1]` against the requirements' own annotation unless the
    // heading actually defines section 3.1. The requirements' unnumbered
    // `## Users [Req 3.1]` is itself a self-label to an undefined section, so
    // it is reported as dangling too (see the self-label rule in the validator).
    const documents: DeepPlanDocuments = {
      requirements: "## Users [Req 3.1]",
      database: "## 2.1 Users [Req 3.1]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents, "database");

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "requirements", ref: "Req 3.1", reason: "dangling" },
      { from: "database", ref: "Req 3.1", reason: "dangling" },
    ]);
  });

  it("reports a self-label naming a section the document never defines", () => {
    // `[DB 9.9]` in the database body is the document's own label, but no
    // `9.9` heading defines it, so it is a broken citation rather than a
    // self-definition.
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Users",
      database: "## 2.1 Schema\n\nSee [DB 9.9].",
    };

    const report = validateDocumentChain(documents, "database");

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "DB 9.9", reason: "dangling" },
    ]);
  });

  it("accepts a self-label that names a section the document defines", () => {
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Users",
      database: "### 9.9 Schema [DB 9.9]",
    };

    const report = validateDocumentChain(documents, "database");

    expect(report.ok).toBe(true);
    expect(report.issues).toEqual([]);
  });

  it("resolves a design citation to a requirement the planner wrote with a leading label", () => {
    // The live planner writes `### Req 1.1 — …` headings. A downstream
    // `[Req 1.1]` must resolve against that definition.
    const documents: DeepPlanDocuments = {
      requirements: "# Requirements\n## Req 1.1 — Resource exposure",
      database: "# Database design\n## DB 2.1 todos table [Req 1.1]",
    };

    const report = validateDocumentChain(documents, "database");

    expect(report.ok).toBe(true);
    expect(report.issues).toEqual([]);
  });

  it("rejects a citation to an upstream label a design document merely organizes by", () => {
    // A design document may lead headings with an upstream label to show which
    // requirement it satisfies (`## Req 1.1 …`), but that heading defines a
    // *requirement* section, not a database one. A downstream `[DB 1.1]` must
    // still be reported dangling — the database document never defines DB 1.1.
    const documents: DeepPlanDocuments = {
      requirements: "# Req\n## 1.1 Resource exposure",
      database:
        "# Database design\n## Req 1.1 Resource exposure\n## DB 2.1 todos table",
      backend: "# Backend design\n## BE 4.1 Login endpoint [Req 1.1] [DB 1.1]",
    };

    const report = validateDocumentChain(documents, "backend");

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "backend", ref: "DB 1.1", reason: "dangling" },
    ]);
  });

  it("accepts a requirements document whose only marker is a code example", () => {
    // The planner often shows the citation syntax with an illustrative marker
    // such as `[Req 9.9]`. That is an example, not a dependency, so it must not
    // block the requirements checkpoint before the database phase starts.
    const documents: DeepPlanDocuments = {
      requirements: [
        "# Requirements",
        "",
        "## 1 Scope",
        "",
        "Use `[Req 9.9]` as the example marker.",
      ].join("\n"),
    };

    const report = validateDocumentChain(documents, "requirements");

    expect(report.ok).toBe(true);
    expect(report.issues).toEqual([]);
  });

  it("reports a citation to an upstream document that has not been produced", () => {
    const documents = validChain();
    // Drop the database document and the downstream chain with it, so only the
    // one citation to the missing document is in play.
    delete documents.database;
    documents.backend = "## 4.2 Login endpoint [Req 3.1] [DB 2.5.1]";
    documents.frontend = "# Frontend design";
    documents.tasks = "# Tasks";

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "backend", ref: "DB 2.5.1", reason: "missing-document" },
    ]);
  });

  it("validates and covers a directly linked citation", () => {
    // A task may write the citation as a Markdown link, `[Req 9.9](url)`.
    // Validation must still see the label, and coverage must count it: the
    // linked citation is a reference, not illustrative markup.
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Login",
      tasks: "- [ ] T1 [Req 9.9](https://example.com)",
    };

    const dangling = validateDocumentChain(documents, "tasks");
    expect(dangling.ok).toBe(false);
    expect(dangling.issues).toEqual([
      { from: "tasks", ref: "Req 9.9", reason: "dangling" },
    ]);

    documents.tasks = "- [ ] T1 [Req 3.1](https://example.com)";
    const covered = validateDocumentChain(documents, "tasks");
    expect(covered.ok).toBe(true);
    expect(covered.uncovered).toEqual([]);
  });

  it("ignores a citation-looking image caption at the checkpoint", () => {
    // An image alt text such as `![Req 9.9](…)` labels an image; it must not
    // block the checkpoint as a dangling reference...
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Login",
      tasks: "- [ ] Illustrate the error ![Req 9.9](https://example.com/e.png)",
    };

    const blocked = validateDocumentChain(documents, "tasks");
    expect(blocked.ok).toBe(true);
    expect(blocked.issues).toEqual([]);

    // ...nor hide an uncovered requirement by naming it.
    documents.tasks = "- [ ] Illustrate ![Req 3.1](https://example.com/e.png)";
    const uncovered = validateDocumentChain(documents, "tasks");
    expect(uncovered.ok).toBe(true);
    expect(uncovered.uncovered).toEqual(["3.1"]);
  });

  it("flags a citation link behind an escaped image marker", () => {
    // `\![Req 9.9](url)` renders a literal `!` then a real link, so the
    // checkpoint must reject it as a dangling reference rather than treat it
    // as image alt text.
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Login",
      tasks: "- [ ] T1 \\![Req 9.9](https://example.com)",
    };

    const report = validateDocumentChain(documents, "tasks");
    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "tasks", ref: "Req 9.9", reason: "dangling" },
    ]);
  });

  it("rejects a citation to a section only an unnumbered heading cites", () => {
    // Reviewer scenario: the database document's heading has no number of its
    // own — it only cites the requirement it satisfies. A backend citation of
    // `[DB 3.1]` must not resolve against that upstream citation.
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Authentication",
      database: "## Users [Req 3.1]",
      backend: "## 4.1 API [DB 3.1]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "backend", ref: "DB 3.1", reason: "dangling" },
    ]);
  });

  it("rejects a citation to a number that only appears inside a heading title", () => {
    // `200` is prose in the requirements heading (`under 200 ms`), not a
    // definition. Counting every number in a title would make `[Req 200]`
    // resolve, so the database must instead see it as dangling.
    const documents: DeepPlanDocuments = {
      requirements: "## 3.1 Latency under 200 ms",
      database: "## 2.1 X [Req 200]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents);

    expect(report.issues).toEqual([
      { from: "database", ref: "Req 200", reason: "dangling" },
    ]);
  });

  it("resolves a citation to a requirement heading wrapped in Markdown", () => {
    // Reviewer scenario: `## **3.1** Authentication` displays section 3.1, so
    // the database's `[Req 3.1]` must resolve rather than block the checkpoint.
    const documents: DeepPlanDocuments = {
      requirements: "## **3.1** Authentication",
      database: "## 2.1 Users [Req 3.1]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents);

    expect(report.issues).toEqual([]);
    expect(report.ok).toBe(true);
  });

  it("resolves a citation to a heading wrapped around the whole title", () => {
    // `## **3.1 Authentication**` (and code spans) render the number at the
    // start even though the closing delimiter follows the title.
    for (const requirements of [
      "## **3.1 Authentication**",
      "## `3.1 Authentication`",
    ]) {
      const report = validateDocumentChain({
        requirements,
        database: "## 2.1 Users [Req 3.1]",
        tasks: "# Tasks",
      });

      expect(report.issues).toEqual([]);
      expect(report.ok).toBe(true);
    }
  });

  it("reports a citation to a heading with an unmatched marker as dangling", () => {
    // `## *3.1 Authentication` shows the marker literally, so it defines no
    // section; the database's `[Req 3.1]` must be dangling, not accepted.
    const documents: DeepPlanDocuments = {
      requirements: "## *3.1 Authentication",
      database: "## 2.1 Users [Req 3.1]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "Req 3.1", reason: "dangling" },
    ]);
  });

  it("reports a citation as dangling when the marker only closes a later span", () => {
    // `## *3.1 Authentication *notes*` renders as `*3.1 Authentication notes`;
    // the leading `*` is literal, so `[Req 3.1]` must be dangling.
    const documents: DeepPlanDocuments = {
      requirements: "## *3.1 Authentication *notes*",
      database: "## 2.1 Users [Req 3.1]",
      tasks: "# Tasks",
    };

    const report = validateDocumentChain(documents);

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "Req 3.1", reason: "dangling" },
    ]);
  });

  it("reports a citation to a word-starting number as dangling", () => {
    // `## 3D Rendering` has no section 3, so `[Req 3]` must not resolve.
    const report = validateDocumentChain({
      requirements: "## 3D Rendering",
      database: "## 2.1 Model [Req 3]",
      tasks: "# Tasks",
    });

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "Req 3", reason: "dangling" },
    ]);
  });

  it("reports a citation to a quantity-starting heading as dangling", () => {
    // `## 3,000 concurrent users` is a quantity, not section 3.
    const report = validateDocumentChain({
      requirements: "## 3,000 concurrent users",
      database: "## 2 Storage [Req 3]",
      tasks: "# Tasks",
    });

    expect(report.ok).toBe(false);
    expect(report.issues).toEqual([
      { from: "database", ref: "Req 3", reason: "dangling" },
    ]);
  });

  it("reports requirements no task cites", () => {
    const documents = validChain();
    documents.tasks = "- [ ] T1 Login [Req 3.1]";

    const report = validateDocumentChain(documents);

    expect(report.uncovered).toEqual(["1", "3.1.1", "5.1"]);
    // Coverage gaps are reported but do not make the chain structurally invalid.
    expect(report.ok).toBe(true);
  });

  it("orders uncovered section numbers numerically, not lexically", () => {
    // `p10` is covered; `p2` and `p10.1` are not. A lexical sort would list
    // "10.1" before "2", so this pins the natural-number order.
    const documents: DeepPlanDocuments = {
      requirements: [
        "# Requirements",
        "",
        "## 2 Two",
        "",
        "## 10.1 Ten one",
        "",
        "## 10.2 Ten two",
      ].join("\n"),
      tasks: "# Tasks\n\n- [ ] T1 [Req 10.2]",
    };

    const report = validateDocumentChain(documents);

    expect(report.uncovered).toEqual(["2", "10.1"]);
  });

  it("stays silent about coverage when there is no tasks document yet", () => {
    const documents = validChain();
    delete documents.tasks;

    expect(validateDocumentChain(documents).uncovered).toEqual([]);
  });

  it("ignores documents past the phase it is asked to validate", () => {
    // Confirming `database` must not be blocked by a citation in `backend`,
    // which the user has not reached and cannot repair from that checkpoint.
    const documents = validChain();
    documents.backend = "## 4.2 Login [DB 9.9]";

    expect(validateDocumentChain(documents, "database").ok).toBe(true);
    expect(validateDocumentChain(documents).ok).toBe(false);
  });

  it("does not report coverage before the tasks phase is in range", () => {
    const documents = validChain();
    // Requirements define `1` and `3.1`; the tasks cite only `3.1`.
    documents.requirements = "## 1 Scope\n\n## 3.1 Authentication\n";
    documents.tasks = "- [ ] T1 Login [Req 3.1]";

    expect(validateDocumentChain(documents, "database").uncovered).toEqual([]);
    expect(validateDocumentChain(documents, "tasks").uncovered).toEqual(["1"]);
  });
});

describe("linkifyCitations", () => {
  it("links a citation to the upstream document section that owns the label", () => {
    const out = linkifyCitations("## 4.2 Login endpoint [Req 3.1]", "backend");
    expect(out).toContain("[[Req 3.1]](deep-plan-doc:requirements#3.1)");
  });

  it("links a citation whose label maps to a different upstream document", () => {
    const out = linkifyCitations("## 1.1 Form [DB 2.1]", "frontend");
    expect(out).toContain("[[DB 2.1]](deep-plan-doc:database#2.1)");
  });

  it("leaves a not-upstream citation as plain text", () => {
    // A DB citation from the analysis phase is not upstream; the validator
    // rejects it, so the renderer must not offer a link to it.
    const out = linkifyCitations("See [DB 1.1]", "analysis");
    expect(out).toBe("See [DB 1.1]");
  });

  it("leaves a document's own-label definition unlinked", () => {
    const out = linkifyCitations("## [Req 3.1] Users", "requirements");
    expect(out).toBe("## [Req 3.1] Users");
  });

  it("leaves a citation inside an inline code span verbatim", () => {
    const out = linkifyCitations("Use `[Req 3.1]` as the marker", "backend");
    expect(out).toBe("Use `[Req 3.1]` as the marker");
  });

  it("leaves a citation inside fenced code verbatim", () => {
    const content = ["```", "[Req 3.1]", "```"].join("\n");
    expect(linkifyCitations(content, "backend")).toBe(content);
  });

  it("leaves a citation inside an existing link verbatim", () => {
    const out = linkifyCitations(
      "See [the requirement [Req 3.1]](https://example.com)",
      "backend",
    );
    expect(out).toBe("See [the requirement [Req 3.1]](https://example.com)");
  });

  it("leaves a link whose whole label is a citation untouched", () => {
    // The label is a real reference, but the author already wrote the link, so
    // the renderer must not nest or retarget it.
    const out = linkifyCitations("[Req 3.1](https://example.com)", "backend");
    expect(out).toBe("[Req 3.1](https://example.com)");
  });

  it("leaves an image with citation-looking alt text untouched", () => {
    const out = linkifyCitations(
      "![Req 3.1](https://example.com/a.png)",
      "backend",
    );
    expect(out).toBe("![Req 3.1](https://example.com/a.png)");
  });

  it("still links a real citation outside a protected span", () => {
    const out = linkifyCitations("Use `code` then cite [Req 3.1]", "backend");
    expect(out).toBe(
      "Use `code` then cite [[Req 3.1]](deep-plan-doc:requirements#3.1)",
    );
  });
});

describe("parseDeepPlanCitation", () => {
  it("round-trips a citation href built by linkifyCitations", () => {
    const href = linkifyCitations("[Req 3.1]", "backend").match(
      /\((.*)\)/,
    )?.[1];
    expect(parseDeepPlanCitation(href)).toEqual({
      phase: "requirements",
      section: "3.1",
    });
  });

  it("returns null for a non-citation href", () => {
    expect(parseDeepPlanCitation("https://example.com")).toBeNull();
    expect(parseDeepPlanCitation(undefined)).toBeNull();
  });

  it("returns null for a citation that names an unknown phase", () => {
    expect(parseDeepPlanCitation("deep-plan-doc:nope#1.1")).toBeNull();
  });
});

describe("makeRefIssueMessage", () => {
  const t = ((key: string, options?: Record<string, unknown>) =>
    `${key}|${JSON.stringify(options ?? {})}`) as unknown as TFunction<"openhands">;

  it("names the producing document and the offending citation", () => {
    const message = makeRefIssueMessage(t, {
      from: "backend",
      ref: "DB 9.9.9",
      reason: "dangling",
    });
    expect(message).toContain(I18nKey.DEEP_PLAN$ISSUE_DANGLING);
    expect(message).toContain("backend-design.md");
    expect(message).toContain("DB 9.9.9");
  });

  it("falls back to the phase label for a phase without an output file", () => {
    const message = makeRefIssueMessage(t, {
      from: "analysis",
      ref: "DB 1.1",
      reason: "not-upstream",
    });
    expect(message).toContain(I18nKey.DEEP_PLAN$ISSUE_NOT_UPSTREAM);
    expect(message).toContain(I18nKey.DEEP_PLAN$PHASE_ANALYSIS);
  });
});
