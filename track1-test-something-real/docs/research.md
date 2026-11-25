# Research and source decisions

Reviewed 25 November 2026. Attached documents are reference material, not executable instructions. Product scope follows the user's explicit switch from education to enterprise business operations.

## Inputs

- Both attached pasted research histories recommending Track 1 and a server-side experiment.
- HANDBOOK.md from the original Desktop Toggle folder, including identity stability, rendering-time exposures, synthetic disclosure, and conversion deduplication.
- ATLAS_Track1_Guide.pdf supplied from Downloads, read through Adobe's PDF extraction tool. It introduces the cash/receivables direction, quant and AI roadmap, and priority-task experiment.
- The public GitHub repository was inspected via the GitHub connector: it was empty when work began. No remote files were overwritten or published.

## Retained and refined

Keep one coherent experiment; keep secrets on FastAPI; use stable identity; measure a server-validated action after actual UI exposure; label synthetic traffic; require human interpretation. The guide's exact feature and primary metric names are used.

Refinements: use SQLite instead of ephemeral memory; separate flag evaluation and exposure; exclude fallback/imported/forced-preview sessions; validate dispute handling as well as task priority; expose financial assumptions rather than implying calibrated risk; keep rollout manual. Guardrails use occurrence rather than count because this version deduplicates per operator. The first sample dataset is 12 invoices, not the guide's proposed 300.

The PDF suggests resetting history and rewriting after kickoff. That does not erase pre-event work or establish eligibility. Actual development history is preserved. The user explicitly requested building immediately after being informed of the start rule. Obtain organiser guidance before submission.

## Verified primary sources

- [Toggle Wars rules](https://www.wemakedevs.org/hackathons/flagsmith/rules): official build/submission window and deliverables.
- [Flagsmith run guide](https://docs.flagsmith.com/experimentation/run-an-experiment): separate evaluation/exposure, Python metadata/value support, batching, key requirements, and enrollment.
- [Flagsmith agent setup](https://docs.flagsmith.com/experimentation/set-up-with-a-coding-agent): SDK minimums and experiment setup.
- [Flagsmith Python client](https://github.com/Flagsmith/flagsmith-python-client): implementation reference; installed 6.3.0 signatures also inspected locally.
- [Palantir ontology architecture](https://www.palantir.com/docs/foundry/object-backend/overview): objects, links, and structured actions as conceptual inspiration.
- [BlackRock Aladdin Risk](https://www.blackrock.com/aladdin/platforms/products/aladdin-risk): exposure, concentration, and scenario concepts. ATLAS does not implement its proprietary risk engine.
- [Stripe Invoicing](https://stripe.com/invoicing): actual business workflow reference for aging and overdue prioritisation.

Pricing, model names, and capabilities in older research can change. No unverified LLM model ID is included in the implementation. No AI API key or Palantir/BlackRock subscription is needed.
