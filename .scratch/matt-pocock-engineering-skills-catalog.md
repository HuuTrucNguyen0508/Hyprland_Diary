# Matt Pocock engineering skills — compact catalog

Source: https://github.com/mattpocock/skills/tree/main/skills/engineering  
Read: each skill’s `SKILL.md` (+ engineering README routing).  
Invocation: **user-invoked** = `disable-model-invocation: true`; **model-invoked** = agent may reach for it.

Main flow (idea → ship): `grill-with-docs` → (optional `prototype`) → `to-spec`/`to-tickets` (multi-session) or `implement` (single) → `tdd` + `code-review`.  
On-ramps: `triage` (incoming issues), `diagnosing-bugs` (hard bugs), `wayfinder` (foggy multi-session planning).  
Vocabulary layers: `domain-modeling`, `codebase-design`.  
Precondition: `setup-matt-pocock-skills` once per repo.

---

## ask-matt
**Purpose:** Router over this repo’s skills/flows; maps situations to the right skill path.  
**When:** Don’t remember which skill/flow fits.  
**When not:** Already know the skill; mid-execution of another skill.  
**Projects:** Any repo using these skills (esp. first time / fuzzy “where do I start?”).

## code-review
**Purpose:** Two-axis review of `fixed-point...HEAD`: Standards (repo docs + Fowler smells) and Spec (originating issue), via parallel sub-agents.  
**When:** Review branch/PR/WIP; after `implement`; “review since X”.  
**When not:** No fixed point / empty diff; need design grilling (use grill/domain skills).  
**Projects:** Any git repo with coding standards and/or issue-linked specs; needs `docs/agents/issue-tracker.md`.

## codebase-design
**Purpose:** Shared vocabulary for deep modules (module, interface, depth, seam, adapter, leverage, locality).  
**When:** Designing/improving interfaces, seams, testability, AI-navigability; pulled by TDD / architecture skills.  
**When not:** Pure feature coding with no shape questions; domain glossary work (`domain-modeling`).  
**Projects:** Any codebase being modularized; language-agnostic design reference.

## diagnosing-bugs
**Purpose:** Hard-bug / perf loop: build red feedback loop → minimise → hypothesise → instrument → fix + regression → cleanup.  
**When:** “Diagnose/debug”; intermittent/flaky/regression; first glance failed.  
**When not:** Trivial one-line bugs; theorising without a red loop; use `tdd` alone for simple test-first fixes.  
**Projects:** Apps/services with runnable loops (tests, HTTP, CLI, browser, bisect); hands off to architecture skill if no good regression seam.

## domain-modeling
**Purpose:** Actively sharpen domain language: challenge terms, stress scenarios, update `CONTEXT.md` / ADRs inline.  
**When:** Terminology disputes; writing/editing CONTEXT/ADRs; driven by grill/triage/wayfinder.  
**When not:** Just *reading* CONTEXT for vocabulary; implementation/spec writing without naming work.  
**Projects:** Domain-heavy apps (esp. DDD-ish); single- or multi-context layouts.

## grill-with-docs
**Purpose:** Relentless interview that also builds domain docs (CONTEXT + ADRs) via `grilling` + `domain-modeling`.  
**When:** Sharpen a plan/design **in a working directory**; start of main flow.  
**When not:** No repo (use grill-me/grilling outside this pack); already-sharp specs ready for `to-spec`.  
**Projects:** Any repo that should keep a durable glossary/paper trail.

## implement
**Purpose:** Build from spec/tickets: drive `/tdd` at agreed seams, typecheck/tests, `/code-review`, then commit.  
**When:** Spec or ready tickets exist; pick up `ready-for-agent` work.  
**When not:** Idea still fuzzy (grill first); foggy mega-effort (wayfinder → to-spec first).  
**Projects:** Spec-driven agent coding with tests; needs tracker setup.

## improve-codebase-architecture
**Purpose:** Scan for deepening opportunities → visual HTML report → grill chosen candidate (with domain updates).  
**When:** Spare time for agent-friendly architecture; after bug post-mortem finds no seam.  
**When not:** Shipping a feature; force-refactoring against ADRs without real friction.  
**Projects:** Mature codebases with hot spots; benefits from CONTEXT.md + codebase-design vocab.

## prototype
**Purpose:** Throwaway code to answer one design question (logic/state HTML demo or UI variations).  
**When:** State/logic hard on paper; explore UI looks; main-flow detour.  
**When not:** Production feature work; questions already settled; agent could decide from docs alone.  
**Projects:** Frontend/state-machine-heavy apps; capture on `prototype/<name>` branch as primary source.

## research
**Purpose:** Background agent investigates against primary sources; writes cited Markdown into the repo.  
**When:** Docs/API facts needed; reading legwork while you continue.  
**When not:** Opinion synthesis from blogs; replaces grilling (feeds into grill instead).  
**Projects:** Any; especially integrations/APIs with official docs/specs.

## resolving-merge-conflicts
**Purpose:** Resolve in-progress merge/rebase hunk-by-hunk by intent from primary sources; finish (never `--abort`).  
**When:** Already mid-conflict.  
**When not:** Planning merges; “should we rebase?” strategy debates.  
**Projects:** Any git workflow with concurrent branches.

## setup-matt-pocock-skills
**Purpose:** One-time per-repo config: issue tracker, triage labels, domain doc layout → `docs/agents/*` + AGENTS/CLAUDE block.  
**When:** Before first use of engineering flows.  
**When not:** Already configured (edit `docs/agents/*.md` instead); mid-feature.  
**Projects:** GitHub/GitLab/local-markdown trackers; solo or team; mono or single-package.

## tdd
**Purpose:** Red→green vertical slices at pre-agreed seams; behaviour tests, not implementation coupling.  
**When:** Build/fix test-first; “red-green-refactor”; integration tests at seams.  
**When not:** Unconfirmed seams; bulk-write-all-tests-first; refactor during the loop (review stage).  
**Projects:** Testable codebases with clear interfaces; pairs with codebase-design.

## to-spec
**Purpose:** Synthesize current conversation into a tracker-published spec (no interview); label `ready-for-agent`.  
**When:** Idea grilled/clear; multi-session build needs a durable plan.  
**When not:** Still need grilling; tiny single-session implement.  
**Projects:** Issue-tracked repos post-setup; domain glossary expected.

## to-tickets
**Purpose:** Break plan/spec/conversation into tracer-bullet tickets with blocking edges (local files or native tracker links).  
**When:** After spec (or rich plan); multi-ticket / parallelizable work.  
**When not:** Single small implement; wide refactors forced into fake vertical slices (use expand–contract).  
**Projects:** Agent-parallel delivery; GitHub/Linear/local `.scratch/`.

## triage
**Purpose:** State machine over incoming issues/PRs → category + state; verify; grill; agent-ready briefs.  
**When:** Bug reports / external requests piling up; “what needs attention?”.  
**When not:** Tickets from `to-tickets` (already agent-ready); your own planned work.  
**Projects:** Maintained open/source or product repos with issue inflow; optional external-PR surface.

## wayfinder
**Purpose:** Chart foggy multi-session efforts as a map of **decision** tickets; resolve one-at-a-time until route clears, then hand off to `to-spec`.  
**When:** Greenfield / huge feature bigger than one session; destination unclear.  
**When not:** Well-scoped features; skip straight to implement without collapsing map → spec.  
**Projects:** Large planning efforts on a configured tracker (`wayfinder:map` + typed child tickets).

## wizard
**Purpose:** Author interactive bash wizard (from template) for human-only steps: secrets, dashboards, cutovers.  
**When:** Provisioning, credentials/CI secrets, unfamiliar third-party UI, one-off migration needing a human.  
**When not:** Steps the agent can do itself.  
**Projects:** DevOps/setup-heavy repos (`.env`, `gh secret`, third-party SaaS).

---

## Quick routing

| Situation | Skill |
|-----------|--------|
| Which skill? | ask-matt |
| First time in repo | setup-matt-pocock-skills |
| Sharpen idea + docs | grill-with-docs |
| Incoming bug/request | triage |
| Hard bug | diagnosing-bugs |
| Too big / foggy | wayfinder → to-spec → to-tickets → implement |
| Multi-session clear idea | to-spec → to-tickets → implement |
| Single-session clear work | implement (→ tdd, code-review) |
| Design question needs runnable answer | prototype |
| Docs/API fact-finding | research |
| Module shape / seams | codebase-design |
| Glossary / ADR | domain-modeling |
| Architecture debt survey | improve-codebase-architecture |
| Mid merge conflict | resolving-merge-conflicts |
| Human-only setup steps | wizard |
