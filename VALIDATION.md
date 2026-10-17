# Validation evidence — 2026-10-16

- Python 3.12, Linux cloud workspace: 20 standard-library unittest cases passed.
- Tested dry-run behavior, active/completed work selection, useful-artifact retention in basic cleanup and removal in final cleanup, scaffolding retention, retained/deliverable exclusion, unknown/ignored preservation, secret-name checks, wrong-root/copy/filename/ambiguous manifests, unsafe paths, symlinks/hard links, restore collisions, idempotence, lock contention, interrupted move recovery, audit inventory, suggestion fingerprint stability, and explicit tracked-artifact final cleanup.
- Tests use disposable fixture repositories, never the user's projects.
- Initial test setup failed because this executor's temporary-directory parent contains an unusable `.git` marker. Tests now initialize explicit fixture repositories rather than weakening the production broken-repository check. Final run: all 20 pass.
- Python compilation passed.
- Pi/OpenCode command paths and argument substitution checked against current primary documentation. No actual Pi/Pi-GUI/OpenCode installation or LLM command execution performed.
- Windows junction/reparse checking is implemented but not tested on a Windows machine. Real Windows integration, locked-file behavior and case-insensitive path behavior require qualification before unattended use.
- Independent review began but stopped at a preview quota limit. This is NOT an independently approved release. The parent completed implementation and fixture tests.
- No unattended cleanup hooks, permanent purge, repository pushes from the cleanup tool or arbitrary ignored-file deletion.

## Packaging validation — 2026-10-17

- Added standard Pi Git-package manifest exposing only skills and prompts, with no install hooks or dependencies.
- Added OpenCode installer using official skill/command directory conventions, an ownership receipt, collision refusal, local-edit refusal and recoverable previous-version backups.
- All 25 unittest cases passed in the Linux cloud workspace: the original 20 cases plus 5 package/install tests (install/update/uninstall, unrelated-file preservation, unowned collision, modified-file refusal and package manifest checks and injected update-failure rollback).
- No user-PC installation, real Pi/OpenCode discovery, Windows qualification, or actual project cleanup performed in this build step. Prior independent cleanup review limitations still apply.
