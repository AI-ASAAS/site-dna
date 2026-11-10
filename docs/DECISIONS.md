# Decisions & Assumptions

This file records every assumption made while implementing the Website Intelligence MVP (Phases 1-9).

## Phase 1 — Project Structure

- **Layout adaptation.** The repository already contained the `site_dna` platform with its own Phases 1-12. Phase 1 of the Website Intelligence MVP is implemented inside that package instead of creating a parallel `website_intel/` tree. The new report contracts live in `src/site_dna/models/`, the timing helper in `src/site_dna/services/timing.py`, and the scan entry point in `src/site_dna/scan.py`.
- **CLI framework.** The existing CLI uses `argparse`. The `scan` subcommand extends that parser rather than introducing Typer.
- **Settings naming.** Existing `crawler_*` settings are left untouched. MVP defaults are exposed as `scan_*` fields (for example `scan_max_pages`) to avoid collisions with the existing crawler configuration.
- **Placeholder scan status.** A Phase 1 report has every module `skipped`, which the Phase 8 status rules do not cover. It is recorded as `scan_status="completed"` until the real pipeline computes status from module outcomes.
- **Permission.** `--i-have-permission` is mandatory. Without it the CLI exits with code 2 before any network access or file write. The report records `permission_attested: true`.
- **Logging.** The existing `setup_logging` (stdout) is preserved for the current CLI. `setup_scan_logging` adds JSON-lines output to `storage/{scan_id}/scan.log` plus human-readable stderr, and both handlers apply the secret-redaction filter. In addition to API-key patterns, `key=` query parameters are redacted.
- **Lazy Gemini import.** The CLI imports the Gemini diagnostics service only inside `run_smoke`, so `scan` and its tests do not require the Google SDK.
- **Lint baseline.** Pre-existing `ruff` findings in unrelated modules were fixed mechanically (unused imports, import order, f-strings, one whitespace line, and dead assignments) so `ruff check .` passes for the phase.
- **Null/array policy.** The report models encode the shared rule: unknown values default to `None`, and every list field defaults to an empty list.
