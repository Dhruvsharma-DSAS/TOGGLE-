# Flagsmith setup and required access

Use your existing **My first project**. A second project is unnecessary. Renaming it ATLAS is optional; do not buy a plan just to create another project.

## What you provide

1. Access your Flagsmith account yourself and select the existing project/environment.
2. Connect the managed experimentation warehouse under the environment's settings. Confirm Connected before relying on events.
3. Obtain a **server-side environment key** under SDK Keys. Place it in the local `.env` file. Never paste it into chat or screenshots.
4. Set the environment variables below, then restart the backend.

```dotenv
ATLAS_MODE=live
FLAGSMITH_SERVER_KEY=your-server-side-key-entered-locally
FLAGSMITH_FLAG=collections_workspace
ATLAS_DB=atlas-live-synthetic.sqlite3
CORS_ORIGINS=http://localhost:5173
```

The checked-in `.env.example` has no secret value. Use a fresh browser workspace when switching modes; the backend refuses to reuse an identity from another mode. Do not place server keys in `VITE_*` variables.

## Configure the experiment

Create an enabled string multivariate feature `collections_workspace`. Default/control value: `control`. Treatment value **and key**: `decision_brief`. Every variation must have its key; the backend checks that key and value match. Ignore the sample `show_demo_button` flag; this app uses its own flag.

Create metrics:

| Event | Aggregation | Direction |
|---|---|---|
| `valid_collection_action` | Occurrence | Increase |
| `valid_collection_action` | Mean of numeric value (seconds) | Decrease |
| `low_priority_action` | Occurrence | Decrease |
| `invalid_action_attempted` | Occurrence | Decrease |

Create the experiment with the hypothesis in experiment-plan.md, 100% eligible rollout, and 50:50 allocation. Launch only after both paths and metrics are ready. Variation definitions lock during an experiment; ending is final.

## Confirm delivery

Open one workspace with a stable operator identity. Confirm an exposure on the experiment page. Save a valid reviewed priority-account task. Confirm the primary event appears under the same identity. SDK acceptance/local counters do not prove that ingestion succeeded. Check warehouse health, enrolled state, event spelling, variation keys, and computed timestamps if data is missing.

The Python 6.3.0 SDK's installed method signatures were inspected: `track_event` and `track_exposure_event` accept numeric `value` and `metadata`. The backend sends each event with `max_buffer_items=1`. Separate flag evaluation/display confirmation follows the official Python example.

Use a dedicated synthetic environment for simulation; add `--allow-live` only when deliberately sending labelled synthetic traffic there. Live human and synthetic sessions should not share a statistical experiment.

No organisation/admin key is needed for this implementation. Results are reviewed manually with the dashboard and JSON evidence template. Automatic rollout and results fetching are future work. Deployment later needs your chosen host account, configured environment variables, persistent backend storage, and a frontend `/api` reverse proxy to the backend (Vite's development proxy does not exist in a static production build).

References: [Run an experiment](https://docs.flagsmith.com/experimentation/run-an-experiment), [Coding-agent setup](https://docs.flagsmith.com/experimentation/set-up-with-a-coding-agent).
