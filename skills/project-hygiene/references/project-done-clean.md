# ProjectDoneClean

This command means the owner explicitly declares total project completion, not merely completion of a task or model turn. Ask if that is unclear. It must not be invoked automatically.

Perform the read-only ProjectManifestAudit first and resolve uncertain/needed-file classifications before applying cleanup. Review the manifest for development artifacts that have outlived their purpose. Explicitly reclassify only artifacts the owner wants removed as disposable and reclassify anything essential to retained. Do not reinterpret all ignored/untracked files as trash. Preserve finished product/source/assets, build recipes, credentials, useful data and anything unclassified. Keep a compact test-result summary and reproducibility recipe where comparison matters; retaining huge raw output is not mandatory.

Preview:
`python <skill>/scripts/project_hygiene.py --root <exact-root> done --owner-confirmed`

Final cleanup includes explicitly disposable records from any work state, including Git-tracked disposable scaffolding. Tracked removals appear as working-tree deletions; the tool neither stages nor commits nor pushes them. Warn about those deletions before applying. A disposable record marked useful is included: this flag means useful during development, not permanent retention. Essential files must use a retained category.

On the owner's authorized invocation, add `--apply`. This removes all qualifying declared artifacts, not every file in the project. Report preserved categories and unknown files' exclusion, batch ID and restore instructions. Empty directories are left intact.

Recoverable quarantine still occupies disk. For real space reclamation, the owner can review and permanently delete the selected quarantine batch through their normal OS tools later. Permanent deletion is not provided by this tool and cannot be undone by it. No unattended expiry or purge.
