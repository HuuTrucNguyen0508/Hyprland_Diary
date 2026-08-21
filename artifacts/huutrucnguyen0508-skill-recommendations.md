# HuuTrucNguyen0508 — Matt Pocock skill recommendations

Sources:
- `artifacts/huutrucnguyen0508-repo-skill-fit-catalog.md`
- `.scratch/matt-pocock-engineering-skills-catalog.md`

Portfolio shape: solo engineer; many **active multi-service / Next prototypes** + **homelab IaC/ops**; several **frozen learning/academic** repos. Skills pay off where work is ongoing, multi-session, and agent-driven — not on one-shot notebooks or tutorial clones.

---

## 1. Portfolio-wide TOP skills (ranked)

| Rank | Skill | Why it fits this portfolio |
|------|--------|----------------------------|
| 1 | **setup-matt-pocock-skills** | Precondition. Active repos need tracker + `CONTEXT.md` layout before grill/spec/implement. Run once per *active* repo (local markdown is fine for solo). |
| 2 | **grill-with-docs** | Highest leverage start: UniversalPaperclip, Localtion, Overall_Infra, Crawler, BrewBook, CookingWFriend all need durable domain language (pods↔processors, places/owners, swarm bots, novel jobs, recipes). |
| 3 | **diagnosing-bugs** | Matches real work modes: K8s/Convex/Inngest flakes, Electron PDF pipelines, Hyprland/TURZX hardware, compose/homelab regressions. Forces red loops instead of vibe-debugging. |
| 4 | **implement** (+ **tdd**, **code-review**) | Core ship loop for every active product repo. Spec/tickets → vertical TDD at seams → two-axis review. Treat tdd/code-review as required satellites of implement. |
| 5 | **codebase-design** | Multi-service and monorepo surfaces (Paperclip services, Localtion web+mobile, Overall_Infra apps, PDF_Tool pipelines) need deep-module / seam vocabulary for agent-navigable code. |
| 6 | **to-spec** → **to-tickets** | Active prototypes regularly exceed one context window; tracer-bullet tickets with blockers fit Paperclip stages, Localtion marketplace slices, Overall_Infra platform+apps. |
| 7 | **wizard** | Homelab/cloud-heavy: Grafana Cloud, Convex, Supabase, AWS, GitLab CI secrets, Tailscale, Vercel — human-only credential/dashboard steps recur. |
| 8 | **research** | Dense third-party surfaces (Firecrawl, Convex, K8s, Electron, Inngest, Better Auth, OTel). Background cited notes beat re-asking the model. |

**Honorable (install when needed, not day-one):** `domain-modeling` (pulled by grill), `prototype` (UI/game-state questions), `improve-codebase-architecture` (after friction accumulates), `ask-matt` (router once the pack is installed), `wayfinder` (only mega-fog efforts).

---

## 2. Per major repo / cluster — recommendations + triggers

### Cluster A — Active multi-service products
**Repos:** UniversalPaperclip, Overall_Infra, Localtion

| Skill | Use when |
|--------|----------|
| setup-matt-pocock-skills | First agent session in the repo |
| grill-with-docs | New feature/area; fuzzy game/platform/marketplace concepts |
| domain-modeling | Overloaded terms (“service”, “place”, “swarm”, “processor”) |
| wayfinder | Destination foggy *and* >1 session (e.g. Paperclip full K8s+agent loop; Overall_Infra platform redesign) |
| to-spec / to-tickets | Idea clear but multi-slice (auth+map+messaging; Terraform module + app) |
| implement / tdd / code-review | Ticket ready; ship a vertical slice |
| codebase-design / improve-codebase-architecture | Shallow adapters, hard-to-test reconciler/bot seams, spare refactor time |
| diagnosing-bugs | Intermittent agent/pod/metrics, HPA, OTel, bot load failures |
| prototype | Game balance / state machines (Paperclip); map+messaging UX (Localtion) |
| research | Convex/K8s/Grafana/Terraform primary docs |
| wizard | Cluster bootstrap, Grafana Cloud, secrets, LoadBalancer/smoke cutovers |

### Cluster B — Active app products (single-ish stack)
**Repos:** Crawler, CookingWFriend, BrewBook_Truc_Hamouz, PDF_Tool, signalist_stock-app

| Skill | Use when |
|--------|----------|
| setup + grill-with-docs | Domain still implicit (crawl jobs, invites, recipes, PDF modes) |
| to-spec / to-tickets / implement | Multi-session features (job cancel/retry; OCR+legal; AI remix) |
| tdd / code-review | Job APIs, auth, Drizzle/Supabase schemas, PDF pipelines |
| diagnosing-bugs | Firecrawl/Inngest flakes; Electron/OCR regressions; Blob/auth bugs |
| prototype | Library UX, recipe feed, PDF tool UI modes |
| research | Firecrawl, NextAuth/Better Auth, pdf-lib/PDF.js, OpenAI APIs |
| wizard | Vercel/Supabase/OpenAI secrets; NSIS/packaging env (PDF_Tool) |
| codebase-design | PDF_Tool especially (dense feature surface → deepen modules) |
| improve-codebase-architecture | After hot-spot friction (Crawler job layer; PDF_Tool pipelines) |

**Crawler vs scraper_with_crawlee:** install/use skills on **Crawler** only; treat crawlee repo as archive.

### Cluster C — Ops / diary / compose
**Repos:** Hyprland_Diary, storage-server

| Skill | Use when |
|--------|----------|
| diagnosing-bugs | TURZX/SDDM/logout flakes; compose networking; Tailscale |
| research | Hyprland/Caelestia/TUR_USB / Docker primary docs |
| grill-with-docs (light) | Only if turning ops notes into durable CONTEXT for agents |
| wizard | One-off greeter/secret/Tailscale procedures worth scripting |
| setup-matt-pocock-skills | Optional; local markdown if agent flows become regular |

**Skip here:** triage, wayfinder, to-tickets (unless a large infra migration is planned). Prefer short diagnose → fix → diary entry.

### Cluster D — Completed IaC / course / deploy demos
**Repos:** stage-autoremediation, Monitoring_et_Autoscaling_de_conteneurs, Real_Estate

| Skill | Use when |
|--------|----------|
| research | Revisiting AWS/Terraform/Ansible/HPA docs for portfolio writeups |
| wizard | Replaying a human cutover for demos |
| diagnosing-bugs | Only if re-running the lab and something breaks |

**Default:** do **not** install the full pack. Archive/docs work ≠ ongoing agent product flow.

### Cluster E — Learning / CI playgrounds / thin starters
**Repos:** yc-directory, Todo_App, acquisitions, Flutter_app_for_reading (light)

| Skill | Use when |
|--------|----------|
| tdd / code-review | Practicing agent ship discipline on small surfaces |
| implement | Tiny guided features |
| research | Framework docs while learning |

**Default:** skills optional; ROI low vs Cluster A/B. Flutter companion: diagnose + research if sync bugs; otherwise leave light.

### Cluster F — One-shot / frozen academic
**Repos:** Hamouz, Projet_Blockchain_Geolocalisation

**Recommendation:** **SKIP** Matt Pocock engineering pack entirely (notebook/ML deliverable; archived sim+Solidity). No ongoing implement/triage surface.

---

## 3. SKIP / low-value skills (portfolio-wide)

| Skill | Verdict | Why |
|--------|---------|-----|
| **triage** | **SKIP (almost always)** | Solo portfolio; little external issue/PR inflow. Own work goes grill → spec/tickets, not triage. Revisit only if a public repo gets real reporter traffic. |
| **wayfinder** | **Low default; selective** | Heavy; only for foggy multi-session destinations (Paperclip stage expansion, Overall_Infra platform fog). Overkill for CookingWFriend-sized features. |
| **resolving-merge-conflicts** | **Defer** | Useful occasionally, not a portfolio differentiator; install when mid-conflict pain appears. |
| **ask-matt** | **Defer / optional** | Helpful router once many skills are installed; not required if you keep this recommendation sheet. |
| **improve-codebase-architecture** | **Later** | High value on PDF_Tool / Paperclip / Localtion *after* CONTEXT + codebase-design exist and hot spots hurt — not install-order #1. |
| Full pack on frozen/learning repos | **SKIP** | Hamouz, blockchain project, yc-directory, Todo_App CI playground: setup tax > benefit. |

---

## 4. Suggested install order

**Phase 0 — pick target repos (don’t boil the ocean)**  
1. UniversalPaperclip  
2. Localtion  
3. Overall_Infra  
4. Crawler *or* CookingWFriend *or* BrewBook (whichever is next to ship)  
5. PDF_Tool (if desktop work resumes)  
Optional later: Hyprland_Diary (diagnose-heavy subset only).

**Phase 1 — foundation (per chosen repo)**  
1. `setup-matt-pocock-skills` (prefer **local markdown** tracker for solo; GitHub if issues already used)  
2. `grill-with-docs` (+ auto `domain-modeling`) → seed `CONTEXT.md`  
3. `ask-matt` (optional) once ≥4 skills are present

**Phase 2 — ship loop**  
4. `implement`  
5. `tdd`  
6. `code-review`  
7. `to-spec`  
8. `to-tickets`

**Phase 3 — friction & depth**  
9. `diagnosing-bugs`  
10. `codebase-design`  
11. `research`  
12. `wizard` (infra/secrets-heavy repos first: Overall_Infra, Paperclip, BrewBook, stage-* only if revived)

**Phase 4 — as needed**  
13. `prototype` — UI/state unknowns  
14. `improve-codebase-architecture` — after hot spots  
15. `wayfinder` — only mega-fog efforts on Cluster A  
16. `resolving-merge-conflicts` — when conflicts bite  
17. **Never prioritize:** `triage` unless public inflow appears

**Minimal viable pack (fastest path):**  
`setup` → `grill-with-docs` → `implement` + `tdd` + `code-review` → `diagnosing-bugs` → add `to-spec`/`to-tickets` when sessions overflow.

---

## One-line cheat sheet

| If you’re… | Reach for |
|------------|-----------|
| Starting agent work in an active repo | setup → grill-with-docs |
| Shipping a known slice | implement / tdd / code-review |
| Spanning multiple sessions | to-spec → to-tickets |
| Lost in platform fog (Paperclip / Overall_Infra) | wayfinder → then to-spec |
| Something flaky in K8s/Electron/ops | diagnosing-bugs |
| Deepening messy modules | codebase-design → improve-codebase-architecture |
| Wiring Grafana/Convex/cloud secrets | wizard |
| Looking up Firecrawl/Convex/K8s facts | research |
| Waiting on random GitHub issues | *(don’t)* triage |
