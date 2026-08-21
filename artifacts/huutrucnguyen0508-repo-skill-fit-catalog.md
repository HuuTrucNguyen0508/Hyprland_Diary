# HuuTrucNguyen0508 — repo catalog for skill-fit

Source: `gh repo view` + README/tree/package manifests (2026-08-20).  
Scope: purpose | stack | maturity | work modes. **No skill recommendations.**

Ranking heuristic (skill-fit surface only): stack breadth, ongoing vs one-shot, docs/agent surface, recent activity — not personal preference.

---

## Top 8 (skill-fit surface)

| Rank | Repo | Why it ranks |
|------|------|--------------|
| 1 | **UniversalPaperclip** | Multi-service K8s + Convex + Next + agent + Grafana; richest ongoing product surface |
| 2 | **Overall_Infra** | Terraform homelab + 3 Next apps + observability + bot load; platform + product |
| 3 | **Localtion** | pnpm monorepo web+Expo+Mongo+Better Auth+OTel; dual-client marketplace |
| 4 | **Crawler** | Firecrawl novel library, NextAuth, Inngest jobs, library APIs — production-shaped app |
| 5 | **PDF_Tool** | Large Electron/Vite PDF toolkit (OCR, legal, AI); dense desktop feature work |
| 6 | **stage-autoremediation** | AWS Terraform + Ansible + Docker + auto-remediation + GitLab CI — full IaC story |
| 7 | **CookingWFriend** | Polished Next 16 + Turso/Drizzle + Better Auth + Blob; clear app CRUD/admin |
| 8 | **BrewBook_Truc_Hamouz** | Next + Supabase + OpenAI + Docker/K8s/Helm/Ansible; recipe + deploy surface |

Honorable: **Hyprland_Diary** (active Linux ops diary), **storage-server** (compose homelab), **scraper_with_crawlee** (Crawler predecessor).

---

## Per-repo catalog

### Hyprland_Diary
- **Purpose:** Personal troubleshooting diary for Hyprland/Caelestia: TURZX USB dashboard, SDDM greeter, logout, Cursor/Zen theme sync.
- **Stack:** Markdown notes + Python (PIL/TUR_USB), Lua (Hypr/Caelestia), Shell, CSS; systemd user units.
- **Maturity:** Active personal ops (pushed 2026-08-20); living config archive, not an app product.
- **Work modes:** docs, config, ops, debugging, hardware/dashboard tuning.

### UniversalPaperclip
- **Purpose:** Idle/incremental “paperclip” game where AI processors map to real K8s pods; services discoverable by AI; metrics to Grafana Cloud.
- **Stack:** Next.js, TypeScript, Convex (+ local Docker Convex), K8s manifests, Grafana Alloy, PowerShell bootstrap scripts, multi-service Dockerfiles.
- **Maturity:** Active prototype / early product (v0.1; pushed 2026-08-04); architecture documented, cluster optional for stage 1.
- **Work modes:** feature, agent/reconciler, infra (kind/kubeadm), observability, game balance, local/cloud Convex ops.

### PDF_Tool
- **Purpose:** Windows Electron PDF toolkit (PDFgear-class): view/edit/annotate/organize/convert/OCR/forms/sign/compress/protect + AI Copilot + legal mode.
- **Stack:** Electron + electron-vite, TypeScript/JS, PDF.js, pdf-lib, optional LibreOffice/qpdf; smoke/legal test scripts.
- **Maturity:** Substantial feature-complete prototype (PR for content-stream edit; pushed 2026-08-01); Windows-focused.
- **Work modes:** desktop feature, PDF pipeline, OCR/AI integration, packaging (NSIS), regression/smoke tests.

### Hamouz
- **Purpose:** Gameloft Data Scientist technical test — predict player final rank (`winRankPercentage`) from post-match stats.
- **Stack:** Jupyter Notebook, Python ML (LightGBM/SHAP etc.), PDF/PPT deliverables, figures/metrics CSV.
- **Maturity:** One-shot interview deliverable (single push 2026-07-27); frozen.
- **Work modes:** research/EDA, modeling, presentation polish (low ongoing product work).

### Localtion
- **Purpose:** Place rental marketplace — owners list spaces; renters browse registered places on a map, interest + messaging.
- **Stack:** pnpm monorepo — Next.js + Tailwind + shadcn (`apps/web`), Expo (`apps/mobile`), MongoDB/Mongoose/Zod shared, Better Auth, Leaflet/OSM, Docker Compose, Grafana OTel LGTM.
- **Maturity:** Active prototype (UI PRs Jul 2026); seed accounts + observability wired.
- **Work modes:** full-stack feature, mobile, maps/UX, auth/roles, observability, seed/data.

### Overall_Infra
- **Purpose:** Homelab Kubernetes platform (Terraform) plus Decide (N-option cards), Swarm bot console, Swarm Report analytics.
- **Stack:** Terraform modules (platform/observability/app), Next.js apps, Prisma/Postgres, Grafana/Loki/Jaeger, Docker, PowerShell/Node bot scripts.
- **Maturity:** Coherent platform prototype (pushed 2026-07-18); documented localhost LoadBalancer URLs and smoke scripts.
- **Work modes:** IaC, K8s ops, app feature, load-gen/bots, dashboards, HPA/perf.

### Crawler
- **Purpose:** “Novel Library” — Firecrawl-powered novel scraper with auth, cloud storage, phone-friendly downloads.
- **Stack:** Next.js (App Router) in `nextjs-backend/`, Firecrawl, NextAuth, Inngest job APIs, SQLite/markdown DB scripts, TypeScript.
- **Maturity:** v2.0 private app (pushed 2026-07-04); successor to crawlee scraper; job cancel/resume/retry APIs present.
- **Work modes:** crawl adapters, job orchestration, auth/library UX, API, deploy (Vercel).

### CookingWFriend
- **Purpose:** Invite-only recipe club for sharing dishes with friends (admin + feed).
- **Stack:** Next.js 16, Turso (SQLite) + Drizzle, Better Auth, Vercel Blob, shadcn/Tailwind, GitHub CI.
- **Maturity:** Polished private prototype (UI polish commits Jul 2026); clear local seed/auth path.
- **Work modes:** product UI, auth/invites, DB schema, admin, photos/Blob.

### stage-autoremediation
- **Purpose:** Internship/cloud project — IaC + config management + auto-remediation for expanding a DB-backed stack on AWS.
- **Stack:** Terraform (AWS modules: network, compute, LB, DNS, IAM), Ansible playbooks, Docker Compose on EC2, Node/JS services, Prometheus/Grafana/Loki/Jaeger, GitLab CI.
- **Maturity:** Completed stage deliverable (public; last push 2025-11); comprehensive README/architecture; not day-to-day product.
- **Work modes:** IaC, Ansible, remediation runbooks, monitoring, CI validation, docs.

### signalist_stock-app
- **Purpose:** Learning stock trading / Signalist-style app (watchlist, stock detail, search).
- **Stack:** Next.js, TypeScript, Better Auth, MongoDB/Mongoose, Inngest, Radix/shadcn, nodemailer.
- **Maturity:** Learning / mid-prototype (private; Oct 2025); default create-next-app README still present.
- **Work modes:** feature pages, auth, data feeds/jobs, UI polish, learning refactors.

### yc-directory
- **Purpose:** YC-style startup directory — learning Next.js (Sanity CMS, auth, startup CRUD).
- **Stack:** Next.js 15, Sanity, next-auth, Sentry, Tailwind/Radix, pnpm.
- **Maturity:** Tutorial/learning clone (private; Oct 2025); short-lived commits.
- **Work modes:** tutorial follow-along, CMS schemas, auth, UI components.

### scraper_with_crawlee
- **Purpose:** Novel chapter crawler (novelbin) for ebook pipeline; early Next backend for markdown store.
- **Stack:** Crawlee, Playwright, Firecrawl JS, Commander CLI, Next.js backend + Docker Compose, JS/TS.
- **Maturity:** Public prototype / precursor to **Crawler** (Sep 2025); dual CLI + web paths.
- **Work modes:** scraper robustness, retry logic, CLI, backend storage, Docker.

### acquisitions
- **Purpose:** Acquisitions CRUD API app with Neon Postgres via Docker (dev proxy + prod cloud).
- **Stack:** Node/JS, Drizzle, Neon, Docker Compose (dev/prod), nginx, Jest, GitHub Actions (lint/test/docker).
- **Maturity:** CI-focused learning project (Sep 2025); strong Docker/Neon docs, smaller product surface.
- **Work modes:** API/CRUD, Docker/Neon wiring, CI/CD, tests.

### Todo_App
- **Purpose:** Monorepo todo (api + web) used heavily as a GitHub Actions / Docker CI playground.
- **Stack:** TypeScript monorepo (`apps/api`, `apps/web`), Docker, Makefile, multiple GHA workflows, Prettier/ESLint.
- **Maturity:** Learning / CI showcase (Sep 2025); README emphasis on workflows over product depth.
- **Work modes:** CI/CD, lint/format, Docker publish, small app features.

### Real_Estate
- **Purpose:** Simplified Kubernetes-ready real-estate listing site (no heavy external deps).
- **Stack:** Next.js 15, TypeScript, Tailwind, Docker, K8s-oriented packaging.
- **Maturity:** Thin starter / demo (Sep 2025; small disk, short commit window).
- **Work modes:** static/SSR pages, containerize, K8s deploy polish.

### storage-server
- **Purpose:** Personal modular Docker Compose storage/homelab stack (file share, apps, monitoring, Tailscale); includes StirlingPDF extras.
- **Stack:** Docker Compose (includes), JS tooling, PowerShell, large vendored/app trees; public.
- **Maturity:** Operational personal infra (Sep 2025); large disk footprint; ops-first.
- **Work modes:** compose ops, service add/remove, networking/Tailscale, backup/monitoring.

### BrewBook_Truc_Hamouz
- **Purpose:** Mobile-first coffee/specialty drink recipes with auth, scrape/remix/AI generation.
- **Stack:** Next.js, Supabase (Auth/Postgres/Storage), shadcn, OpenAI, cheerio, Docker, K8s/Helm, Ansible, PLpgSQL migrations.
- **Maturity:** Feature-rich private app + deploy docs (Aug–Sep 2025); “first app for Truc and Hamouz.”
- **Work modes:** recipe product, AI/RAG, Supabase schema, K8s/Ansible deploy, secrets hygiene.

### Flutter_app_for_reading
- **Purpose:** Flutter novel reader syncing markdown from a backend API (pairs with crawler/library backends).
- **Stack:** Flutter/Dart, Android/iOS scaffolding, SQLite local, markdown rendering.
- **Maturity:** Working mobile companion (Sep 2025); sync/design commits; public.
- **Work modes:** mobile UX, offline reading, API client, theme/progress.

### Monitoring_et_Autoscaling_de_conteneurs
- **Purpose:** University Cloud/Network course project — container monitoring and HPA autoscaling with IaC scripts.
- **Stack:** Shell scripts, Docker Desktop K8s, Helm, Prometheus/Grafana/Redis patterns (screenshots-heavy).
- **Maturity:** Academic deliverable (2024–2025 updates); script + docs oriented.
- **Work modes:** lab reproduction, HPA/alerts, script hardening, course docs.

### Projet_Blockchain_Geolocalisation
- **Purpose:** M1 group project — ns-3 Wi‑Fi sim + trilateration device code + Solidity storage for geolocation on-chain.
- **Stack:** C++ (ns-3 / device code), Solidity, Remix/JS deploy scripts, TypeScript helpers.
- **Maturity:** Archived academic (May 2024; last update Oct 2024); presentation-linked, not maintained product.
- **Work modes:** simulation, smart-contract demo, research writeup (low agent product fit).

---

## Quick matrix

| Repo | Maturity (short) | Primary work modes |
|------|------------------|--------------------|
| Hyprland_Diary | Active personal ops | docs, config, ops |
| UniversalPaperclip | Active multi-service prototype | feature, K8s, agent, o11y |
| PDF_Tool | Dense desktop prototype | Electron feature, PDF/AI |
| Hamouz | One-shot DS test | research, notebook |
| Localtion | Active monorepo prototype | web+mobile, maps, auth |
| Overall_Infra | Homelab platform prototype | Terraform, apps, bots, o11y |
| Crawler | Private v2 app | crawl jobs, library, auth |
| CookingWFriend | Polished private app | product UI, DB, auth |
| stage-autoremediation | Completed internship | IaC, Ansible, remediation |
| signalist_stock-app | Learning prototype | Next features, jobs |
| yc-directory | Tutorial clone | learning Next/Sanity |
| scraper_with_crawlee | Public precursor | crawler CLI, Docker |
| acquisitions | CI/Docker learning | API, Neon, GHA |
| Todo_App | CI showcase | workflows, monorepo |
| Real_Estate | Thin K8s demo | Next + Docker |
| storage-server | Personal compose stack | ops, compose |
| BrewBook_Truc_Hamouz | Deployable recipe app | product + K8s/Ansible |
| Flutter_app_for_reading | Mobile companion | Flutter, sync |
| Monitoring_…_conteneurs | Course project | K8s HPA lab |
| Projet_Blockchain_… | Archived M1 | sim + Solidity |

---

## Notes for coordinator

- All 20 requested repos resolved under `HuuTrucNguyen0508/` via `gh`.
- Private vs public does not change catalog fields; several high-rank repos are private.
- **Crawler** supersedes much of **scraper_with_crawlee** for novel-library work.
- No skill recommendations included (per task).
