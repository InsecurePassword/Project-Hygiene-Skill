# ProjectClean

Use `python <skill>/scripts/project_hygiene.py --root <exact-root> clean` to preview.
Only explicitly disposable, non-useful, untracked files belonging to completed work qualify. Project-wide scaffolding, active work, retained files, deliverables, source and unknown files stay.

Show the candidate count and total bytes. If the user's invocation authorizes this cleanup, run the same command with `--apply`; otherwise request approval. The tool moves candidates into project-local quarantine and returns a restore batch ID. Report the ID and location. Never replace this with `git clean`, glob deletion or directory removal.

Quarantine is recoverable but does not reclaim disk capacity. Nothing is permanently purged automatically. Do not describe the operation as freeing disk space.
