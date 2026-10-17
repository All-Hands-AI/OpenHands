I am an AI agent helping Engel Nyst (@enyst) with project work.

# Maintenance PR publication prerequisites

The user has authorized at most one unmerged maintenance PR to `enyst/playground` targeting `main`. Missing publication authorization is not a blocker. The prepared title and complete body are retained separately; the human-only field remains exactly as in the repository template.

| Source | Exact relevant requirement | Consequence |
|---|---|---|
| `/workspace/.onboarding/start-skill.md:35–39` | “Every PR description, comment, issue body, or other post made as `enyst` must begin with this exact sentence:” followed by `I am an AI agent helping Engel Nyst (@enyst) with project work.` | The prepared body begins with that literal sentence. |
| `AGENTS.md:49` | “The `HUMAN:` section in PR descriptions is reserved for human contributors only. AI agents must not add to, edit, move, or remove it. If validation fails because it is missing or empty, stop and ask the human user to update it in their own words.” | The agent cannot honestly supply the human note. |
| `.github/pull_request_template.md` | `HUMAN:` followed by `<!-- Human contributors: add a short note about your testing. -->` | The actual template has no human statement to preserve other than the untouched blank field/comment. |
| `.github/scripts/check_pr_description.py:374–379` | `The first visible line of the PR description must be `HUMAN:`.` and `Add a short human-written note between `HUMAN:` and `AGENT:`.` | The validator requires at least 20 visible characters of genuine human prose. Its first-visible-line rule conflicts with the required literal attribution prefix. Hiding attribution in a comment is not a resolution. |
| `.github/pull_request_template.md`, Issue Number | “The linked issue must carry the `ready-for-dev` label ... If no such issue exists yet, open one using the Bug or Feature Request template and wait for it to be labeled `ready-for-dev` before opening this PR.” | A fork tracking issue with accepted readiness is required. Upstream-only maintenance references do not satisfy the fork validator. |

These are mandatory local workflow/validator requirements, not a request to reauthorize the audit. The human input needed after independent work is complete is: a short testing note in the human’s own words, and a resolution of the conflicting first-line rules. Separately, the linked fork tracking issue must carry the required readiness label; the validator does not make label application inherently human-only, and no readiness label is added as a side effect of map bookkeeping. No approval statement, testing claim or readiness label will be invented.
