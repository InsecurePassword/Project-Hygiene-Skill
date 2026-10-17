# ProjectManifestAudit

Read-only audit. Resolve the exact project root and run `python <skill>/scripts/project_hygiene.py --root <root> audit`. Do not apply cleanup or rewrite classifications as part of this command.

Check the manifest against actual project use, not just names:
1. Verify root, UUID, filename, Git identity and work states. Report missing files, unknown files, invalid paths and stale records.
2. Inspect source/build/test/import/package references for every disposable candidate; determine whether the product, next implementation, reproducible build or regression comparison still depends on it. Inspect configuration structure without revealing secret values.
3. Check that reusable tests/tools, runtime dependencies, credentials and owner data are not mislabeled disposable. Check project-wide scaffolding is not mistaken for a small completed probe.
4. Distinguish basic-clean candidates from final-clean candidates. A useful disposable artifact is kept by basic cleanup but intentionally removed by final cleanup; change it to retained if it is essential beyond project completion.
5. Flag unregistered files in temporary directories, retained files in disposal-oriented directories, and artifacts outside the prescribed layout. Unknown does not mean disposable.
6. Report each discrepancy with path, evidence, proposed category and confidence. If reference search is inconclusive, recommend retention. List scope/exclusions and avoid claiming that a static search proves safety.

Show a concise summary and any blocking misclassifications. Offer corrections as a separate action; never delete while auditing. Avoid dumping giant logs or inventory lists into model context; inspect targeted sections and save a local report only when needed, registering that report in the manifest.
