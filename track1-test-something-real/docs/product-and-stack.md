# ATLAS product and technical plan

## Idea and buyer

ATLAS is a connected decision workspace for a company's CFO, controller, and operations leads. The first buyer hypothesis is a small or mid-market B2B company whose receivables process still lives in spreadsheets. Validate that hypothesis with finance operators before expanding scope.

A sample workflow: import outstanding invoices → identify overdue and disputed exposure → inspect linked customer invoices → assess a payment delay → review and save the next collection task → export the decision record. This is business operations software with a measurable outcome, rather than a dashboard with disconnected visualisations.

The long-term enterprise direction combines institutional exposure and scenario concepts with connected business objects and controlled actions. BlackRock Aladdin and Palantir are conceptual references, not integrations, affiliations, or capability comparisons.

## First module

| Entity | Current representation | Linked behaviour |
|---|---|---|
| Workspace | Anonymous session | Owns invoices and tasks; isolates sample/imported datasets |
| Customer | Customer name aggregated from invoice rows | Concentration, linked invoices, scenario balance |
| Invoice | ID, balance in integer cents, USD, date, status | Aging, task validation, ranking |
| Dispute | Invoice status | Requires a dispute-review task |
| Task | Invoice, type, note, timestamp | Human approval and audit export |
| Experiment event | Stable visitor, value, metadata, delivery state | Exposure, primary outcome, guardrails |

Customer master records, payments, contacts, assignment to real employees, and ERP writeback are future work. Current audit records cover task creation; they are not immutable compliance logs.

## Stack and rationale

| Layer | Choice | Reason |
|---|---|---|
| UI | React 19, Vite 6.4.6 | Fast local iteration, static production build, explicit state |
| Icons | Lucide React | Consistent lightweight symbols |
| Styling | CSS tokens, DM Sans/Manrope with fallback | Institutional density, responsive views |
| API | FastAPI, Pydantic, Uvicorn | Server validation, typed request schemas, API docs |
| Storage | SQLite | Persistent assignment, cents arithmetic, conversion/task deduplication |
| Flags | Flagsmith Python 6.3.0 | Server-side evaluation, explicit exposures, event metadata |
| Quant | Python standard library, seeded random generator | Repeatable assumptions without unnecessary dependencies |
| Verification | Pytest, httpx, Playwright | API invariants, retries, isolation, user workflow and responsive rendering |
| Traffic | Python HTTP simulator | Same validated endpoints as the app |

Exact frontend dependency graph is in package-lock.json; Python direct versions are in requirements.txt. Vite was updated to 6.4.6 after the initial audit identified issues in 6.4.1.

## Quant contract

The ranking model is assumed incremental collection value per effort hour:

`balance × (P(payment with action) − P(payment without action)) / effort_hours`.

| Task | Without action | With action | Effort hours |
|---|---:|---:|---:|
| Dispute review | 10% | 45% | 1.5 |
| Overdue reminder | 40% | 55% | 0.25 |
| Current follow-up | 70% | 73% | 0.25 |

These probabilities are synthetic assumptions, not causal estimates or default probabilities. A reason line exposes the exact calculation. Top-five accounts are the five highest aggregate invoice priorities for the fixed sample dataset, independent of operator clicks and assignment.

The 30-day Monte Carlo model uses 1,000 independent invoice-receipt draws, seed 42, and the published no-action probabilities. It reports 5th/50th/95th percentile receipts and defines cash-at-risk here as median receipts less 5th-percentile receipts. This is an illustrative distribution under assumptions; it ignores correlated customers, partial payments, historical calibration, and changing economic conditions.

HHI is 10,000 times the sum of squared customer balance shares. It is shown as a descriptive concentration number, with no unsupported credit-risk threshold.

The deterministic delay scenario is `balance × annual funding rate × added days / 365`. It is a sensitivity calculation, not a forecast of actual borrowing needs. All selected-customer balances are included under the stated full-delay assumption.

## Roadmap

1. Complete hosted demo and live Flagsmith delivery proof; run the controlled experiment.
2. Pilot with actual finance operators using consented, non-sensitive data; assess task accuracy and relevance.
3. Add company SSO, tenant-aware access policies, durable encryption/backup policy, role-specific approvals, and a background event worker.
4. Add payment history, customer master data, partial-payment reconciliation, and ERP read-only connectors.
5. Fit and validate payment-time models using censored history; backtest cash simulations and calibrated loss assumptions.
6. Add fact-grounded AI reminder drafts behind a separate `ai_drafts` kill switch, disabled during the core experiment. Evaluate facts and human edits before allowing any outbound integration.
7. Expand to supplier, inventory, and delivery-risk modules only after proving the first workflow useful.

No LLM key is required for version one. Paid plans, email sending, investment execution, and financial-account access are outside the present build.
