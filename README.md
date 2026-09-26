# DevTwin — Pre-Merge Change Simulator

<div align="center">

**Know the impact before you merge.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20Free-4285F4?logo=google&logoColor=white)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

*Built with IBM Bob 2.0 — IBM Bob 2.0 Hackathon Submission*

</div>

---

## What is DevTwin?

DevTwin is an **AI-powered pre-merge software change simulator**. Before you merge a pull request, DevTwin analyzes your proposed change against the full codebase — surfacing hidden dependencies, blast radius, breaking tests, security risks, and coverage gaps — in seconds, not hours.

**The core workflow:**

```
Proposed Change
      ↓
Repository Scan + Dependency Graph  (deterministic, instant)
      ↓
  ┌─────────────────────────────────────┐
  │  Parallel AI Analysis (3 agents)   │
  │  ├─ Risk Analyst                   │
  │  ├─ Test Impact Analyst            │
  │  └─ Documentation Analyst          │
  └─────────────────────────────────────┘
      ↓
Regression Test Generator
      ↓
Verifier (runs real test suite)
      ↓
Final Report + Productivity Metrics
```

---

## The Problem

When you propose a code change, you only see the lines you changed. The real consequences — which modules break, which tests fail, which security invariants are violated — are invisible until after merge, when bugs reach production.

Manual investigation of a single change takes **30–60 minutes**: reading call chains, grepping for callers, running tests, reviewing docs. This work is tedious and consistently skipped under pressure.

## The Solution

DevTwin does this investigation **automatically, in parallel, in ~30 seconds**, giving you an evidence-backed risk report before you click merge.

---

## Live Demo

| Step | What you see |
|---|---|
| Select **Demo Orders** project | Sample e-commerce Python microservice |
| Load prepared change | A small-looking but consequential diff |
| Click **Analyze** | 9-step pipeline runs in real time |
| Blast Radius Graph | Visual map of 7 direct + 12 indirect impacts |
| Risk Findings | 1 CRITICAL security risk + 2 HIGH risks discovered |
| Test Impact | 1 existing test will break — identified precisely |
| Generated Test | AI writes regression test matching project style |
| Verification | 24 tests run and pass |
| Final Report | Evidence-backed verdict: **Do not merge** |

---

## Architecture

```
devtwin/
├── backend/                        ← Python / FastAPI
│   ├── main.py                     ← App entry point + env loading
│   ├── api/router.py               ← REST endpoints + async job queue
│   ├── models/analysis.py          ← Pydantic domain models
│   ├── analysis/                   ← Deterministic code analysis (no AI)
│   │   ├── scanner.py              ← File discovery + filtering
│   │   ├── extractor.py            ← Python AST symbol extraction
│   │   ├── graph.py                ← Dependency graph + BFS blast radius
│   │   └── diff_parser.py          ← Unified diff parser
│   └── agents/                     ← AI-powered reasoning agents
│       ├── orchestrator.py         ← Parallel workflow coordinator
│       ├── dependency_analyst.py   ← Blast radius (deterministic)
│       ├── risk_analyst.py         ← AI risk evaluation
│       ├── test_analyst.py         ← AI test impact analysis
│       ├── doc_analyst.py          ← AI documentation understanding
│       ├── test_generator.py       ← AI regression test generation
│       ├── verifier.py             ← Allowlisted command execution
│       ├── llm_client.py           ← Gemini client + demo fallback
│       └── json_utils.py           ← Robust JSON extraction
├── frontend/                       ← React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx                 ← Root + screen routing
│   │   ├── api.ts                  ← API client + polling
│   │   ├── types/api.ts            ← TypeScript types
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx     ← Project selector + change input
│   │   │   └── AnalysisPage.tsx    ← Live pipeline + tabbed results
│   │   └── components/
│   │       ├── ProgressPipeline.tsx
│   │       ├── SummaryCards.tsx
│   │       ├── BlastRadiusGraph.tsx
│   │       ├── RiskFindings.tsx
│   │       ├── TestImpactPanel.tsx
│   │       ├── GeneratedTestPanel.tsx
│   │       ├── VerificationPanel.tsx
│   │       ├── FinalReport.tsx
│   │       └── MetricsPanel.tsx
└── sample_project/                 ← Demo Orders — synthetic target project
    ├── models.py, auth.py          ← Domain models + authentication
    ├── services/order_service.py   ← Business logic layer
    ├── repositories/               ← Data access layer
    ├── api/routes.py               ← Flask HTTP routes
    ├── tests/                      ← 24 pytest tests (all pass)
    ├── docs/architecture.md        ← Architecture documentation
    └── demo_change.diff            ← Prepared demo change
```

### Design Principle

DevTwin uses **deterministic code** for deterministic problems and **AI reasoning** for reasoning problems:

| Deterministic (fast, reliable) | AI-powered (where it adds value) |
|---|---|
| File scanning + filtering | Understanding a proposed change |
| Python AST parsing | Reasoning about hidden risks |
| Symbol extraction | Identifying semantic test gaps |
| Dependency graph (BFS) | Generating regression tests |
| Test execution | Understanding documentation |
| API routing + validation | Synthesizing evidence into a report |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11+, FastAPI, uvicorn |
| AI Agents | Google Gemini (free tier via `google-genai`) |
| Demo Mode | Pre-computed results — works without any API key |
| Code Analysis | Python AST, custom dependency graph |
| Frontend | React 18, TypeScript 5, Vite |
| Graph Visualisation | Pure SVG (no external chart libraries) |
| Test Runner | pytest |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**
- *(Optional)* Free Google Gemini API key → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

> **No API key? No problem.** DevTwin runs in **Demo Mode** with pre-computed realistic results — full workflow, zero cost.

---

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/devtwin.git
cd devtwin
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

**For live AI** (optional — free Gemini key):
```bash
cp .env.example .env
# Open .env and paste your GEMINI_API_KEY
```

**For demo mode** (no key needed):
```bash
# Nothing to do — just start the server
```

### 3. Set up the frontend

```bash
cd ../frontend
npm install
```

### 4. Run DevTwin

**Terminal 1 — Backend:**
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run start
# Opens http://localhost:3000
```

### 5. Open in browser

Visit **[http://localhost:3000](http://localhost:3000)**

---

## Running the Demo

1. Open DevTwin at [http://localhost:3000](http://localhost:3000)
2. Click **Demo Orders** project card
3. Click **↓ Load Demo Change**
4. Click **⚡ Analyze Change**
5. Watch the 9-step pipeline animate in real time
6. Click nodes in the **Blast Radius Graph** to inspect impacts
7. Read **Risk Findings** — discover the hidden security risk
8. Check **Test Impact** — see which test will break
9. Read **Generated Test** — AI-authored regression test
10. See **Verification Results** — 24 tests pass
11. Read the **Final Report** — evidence-backed verdict
12. Review **Productivity Metrics** — 45 min → 30 seconds

### The Demo Change (what DevTwin discovers)

The change looks innocent:

```diff
- if not order.can_be_updated():
-     raise OrderValidationError(...)
+ if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
+     raise OrderValidationError(...)
```

**DevTwin surfaces 4 hidden consequences:**

| Severity | Finding |
|---|---|
| 🔴 CRITICAL | Admin discount bypass — confirmed orders can now be retroactively discounted |
| 🟠 HIGH | `test_cannot_update_confirmed_order` will break |
| 🟠 HIGH | Undocumented API contract change on `PATCH /orders/<id>` |
| 🟡 MEDIUM | Inventory inconsistency — items replaceable after warehouse commitment |

---

## Running Tests

**Sample project unit tests (24 tests):**
```bash
cd sample_project
python -m pytest tests/ -v
```

**Backend import check:**
```bash
cd backend
python -c "from main import app; print('OK')"
```

**Frontend type check:**
```bash
cd frontend
npm run typecheck
```

---

## Agentic Workflow

The orchestrator runs three AI agents **in parallel** using `asyncio.gather()`:

```python
risk_task = executor.run(analyze_risks, ...)
test_task = executor.run(analyze_tests, ...)
doc_task  = executor.run(analyze_documentation, ...)

risk_findings, test_analysis, doc_insights = await asyncio.gather(
    risk_task, test_task, doc_task
)
```

This reduces total analysis time by ~3× compared to sequential execution.

**Each agent has a single clear responsibility:**

| Agent | Responsibility | Method |
|---|---|---|
| Orchestrator | Coordinate all agents, produce final report | asyncio |
| Dependency Analyst | Compute blast radius via BFS | Deterministic |
| Risk Analyst | Identify security, regression, API risks | AI (Gemini) |
| Test Analyst | Find breaking tests + coverage gaps | AI (Gemini) |
| Documentation Analyst | Extract constraints from README/docs | AI (Gemini) |
| Test Generator | Write regression tests matching project style | AI (Gemini) |
| Verifier | Run allowlisted pytest command | subprocess |

---

## Security

- **No arbitrary command execution** — verifier uses an explicit allowlist
- **Path traversal protection** — all file reads validated against project root
- **No secrets in code** — API key loaded from `.env` (gitignored)
- **Synthetic data only** — no real customer or company data
- **`.env.example` contains only placeholder values** — never real keys

---

## Productivity Metrics

DevTwin shows transparent, honestly labeled metrics:

| Label | Meaning |
|---|---|
| **Measured prototype run** | Directly observed in this analysis run |
| **Baseline estimate** | Typical manual investigation time |

Typical result: **45 minutes → 30 seconds** for the Demo Orders change.

---

## Limitations

- Python projects only (TypeScript/Java/Go analysis not yet implemented)
- In-memory job store — history clears on server restart
- One project analyzed at a time
- Generated test is shown but not auto-executed in the prototype
- AI results depend on Gemini API availability (demo mode always works offline)

---

## IBM Bob 2.0

This project was built entirely using **IBM Bob IDE** as the core development environment:

- Architecture design and planning in Bob Plan mode
- All code implementation via Bob Agent mode
- Parallel subagent tasks for independent analysis components
- Session evidence preserved in `bob_sessions/`

---

## Project Structure (top level)

```
devtwin/          ← Main application
bob_sessions/     ← IBM Bob session evidence (PNG screenshots)
START_BACKEND.bat ← Windows: start backend server
START_FRONTEND.bat← Windows: start frontend
```

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
<strong>DevTwin moves expensive software-change discovery<br>from after-the-fact debugging to before-merge verification.</strong>
</div>
