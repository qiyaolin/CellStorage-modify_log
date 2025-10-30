# History Tree Refactor Plan

## Current Issues
- Template pp/templates/main/history_tree.html is nearly 3k lines with inline scripts, hard to maintain and debug.
- The template uses an undefined Jinja block xtra_head, so required libraries such as D3.js never load.
- Inline JavaScript references non-existent globals (e.g. collaborationManager, nalyticsDashboard), causing runtime errors.
- UI mixes too many experimental features without clear flows, leaving users without a working tree visualization.
- No separation between presentation and logic; everything is embedded in the template which complicates testing.

## Experience Goals
- Provide a dependable workflow: search a batch, review key statistics, inspect lineage visually.
- Deliver fast feedback with clear loading states and actionable empty/error states.
- Keep layout responsive and accessible while matching existing Bootstrap based styling.
- Favor progressive enhancement: work with core /api/batch/<id>/lineage endpoints and gracefully try v2 optimizations.

## Proposed Architecture
- Keep existing Flask route cell_storage.history_tree and data endpoints; avoid breaking API clients.
- Replace the template with a focused structure: selection panel (search, quick lists, batch summary) and visualization panel.
- Move all page logic to a new static module pp/static/js/history_tree.js to isolate state management and rendering.
- Add a lightweight stylesheet for the tree container for better spacing and overflow handling.
- Implement a D3 based renderer that can draw ancestors or descendants; allow toggling and resize handling.
- Add fetch helpers with retry/fallback: prefer /api/v2/.../optimized or /summary, fall back to v1 endpoints on failure.

## Key Interactions
1. User searches or picks a batch -> selection state updates.
2. App loads summary stats and lineage data (with loading indicators).
3. Visualization renders using D3; controls allow switching between ancestors/descendants/full tree and exporting SVG.
4. Errors surface as Bootstrap alerts to keep users informed without blocking the UI.

## Deliverables
- New HTML template with Bootstrap layout, help modal, and placeholders for dynamic content.
- history_tree.js providing state management, data fetching, rendering, and UI bindings.
- Optional history_tree.css for layout refinements.
- Updated documentation here and inline code comments for future maintenance.
