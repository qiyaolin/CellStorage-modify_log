# Repository Guidelines

## Project Structure & Module Organization
- Core Flask server sits in pp/ with blueprints in cell_storage, inventory, pi/printing, shared utilities under shared/, and middleware in services/.
- HTML templates and static assets reside in pp/templates and pp/static; admin tooling is configured in dmin_interface.py.
- Database helpers and import scripts stay at the repo root; migration scripts belong in migrations/ and should mirror dd_batch_id_to_print_jobs.py.
- Front-end workspaces include cellstorage-ui-upgrade/ (Vite React) and cellstorage-mobile/ (React Native TypeScript under src/lib).

## Build, Test, and Development Commands
- python -m venv .venv && .\\.venv\\Scripts\\activate
- pip install -r requirements.txt
- python run.py boots the WSGI app returned by create_app(); lask shell reuses the context defined in 
un.py.
- python migrate_database.py or the targeted file in migrations/ should run before validating schema-impacting changes.
- In web/mobile workspaces, use 
pm install followed by 
pm run dev or 
pm start per the local package.json.

## Coding Style & Naming Conventions
- Adopt 4-space indentation and PEP 8; keep modules scoped to a single blueprint or concern.
- Name Flask views with verb-first snake_case, align template names with their view functions, and group imports standard/library/local.
- TypeScript utilities stay camelCase; components and screens remain PascalCase with one export per file.

## Testing Guidelines
- Current smoke scripts (
eal_browser_test.py, check_csv_import.py) double as fixtures; execute them via python <script> after migrations.
- Add new automated coverage with pytest in a 	ests/ package; prefer 	est_<route>_<behaviour>() names covering happy-path and failure states.
- Document required seed data or feature flags in PR notes so reviewers can reproduce results locally.

## Commit & Pull Request Guidelines
- Follow the concise, imperative convention seen in git log (e.g., Improve mobile pickup flow) and avoid bundling unrelated modules.
- Reference tickets in the first line when available, and flag migrations or environment updates explicitly.
- PR descriptions should list touched blueprints, client bundles, and scripts; attach screenshots or terminal output for UI or data changes.
- Before review, rerun the Flask server and any affected frontend build, and capture follow-up tasks as TODOs or linked issues.

## Configuration & Security Notes
- Secrets live in .env; define SECRET_KEY, local DATABASE_URL, optional CENTRALIZED_PRINTING_ENABLED, and Cloud SQL credentials when targeting production.
- When adding toggles in config.py, document defaults and rollout steps so Operations can replicate the environment safely.

## Route Integrity & Regression Guardrails
- Missing endpoints during the cryovial search refactor stemmed from copy/paste replacements that dropped helper routes (`add_cryovial`, `pickup_selected_vials`, counters, edit/delete handlers) defined below `cryovial_inventory`. Templates still referenced them, producing 404/500 failures post-deploy.
- Always diff full blueprint files after restructuring; avoid truncating tail sections when splicing in new functions. Use `git diff` or `python -m compileall` plus `flask routes` to confirm every registered endpoint survives.
- Before pushing, run `rg "url_for('cell_storage" app/templates/main/cryovial_inventory.html` and verify each endpoint exists in `routes.py`; add a lightweight pytest smoke test that hits critical URLs to surface BuildError regressions.
- Keep backup modules (`routes_current_backup.py`) in sync or retire them once merged to reduce divergence. Prefer refactors driven by smaller helper functions rather than wholesale paste operations.
- Require staging deploy validation of the CryoVial flow (search → add to pick up → pick up confirmation) after backend changes, and document the result in the PR checklist to stop regressions from reaching production.
