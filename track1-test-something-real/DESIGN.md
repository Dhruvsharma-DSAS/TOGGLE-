# ATLAS interface direction

An institutional operations workspace: dark navigation, light working surfaces, restrained green actions, tabular finance data. Chosen from the requested enterprise direction; it is an independent design, not a copy of an inspected corporate product.

## Sections

Navigation establishes the working context; the header names the current task; a dataset strip states provenance; portfolio metrics expose balances; aging and concentration summarise the data; the register leads to reviewed actions. The decision variant adds one top-three prioritisation brief. Relationships, scenarios, audit, and Experiment Lab have distinct tasks.

## Tokens

CSS source of truth: `frontend/src/styles.css`.

- Canvas `--bg: #f6f7f8`; surfaces `--surface: #fff`; borders `--line: #e6eaeb`.
- Body text `--ink: #202c30`; secondary text `--muted: #6b767b`.
- Navigation `--sidebar: #17282c`, muted navigation `--sidebar-ink: #a8b6b9`.
- Actions `--teal: #275e53`; selected surfaces `--teal-soft: #edf3f0`.
- Review `--amber: #906527`, `--amber-bg: #faf1e2`; errors `--red: #a34e49`, `--red-bg: #fbefec`.
- Focus `--orange: #d49a62`; all actionable controls have a focus-visible outline.
- Type: DM Sans body and Manrope headings, with system fallbacks. Compact desktop density and horizontally scrollable data tables on narrow screens.
- Space: 4/8px base; 16/24/40px page and panel rhythm. Radii 4/5/8px, 12px dialogs.
- Icons: Lucide. No fabricated customer logos; sample initials identify fictional accounts.
- Motion: short state changes only; reduced-motion support. One light content theme.

Dialogs support Escape, focus trapping, and restoring focus. Search, selects, and forms have accessible labels; navigation retains accessible text when collapsed.
