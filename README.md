# Project Hygiene

A small, local-only skill and standard-library Python cleanup tool for Pi and OpenCode. No inference server, cloud dependency, background watcher or external Python packages. Python 3.10+ and Git are required.

## Commands

- **/ProjectClean**: recoverably remove explicitly disposable files belonging to completed work. Preserve potentially useful files, Git-tracked files and project-wide scaffolding.
- **/ProjectDoneClean**: after the owner's explicit total-project-completion declaration and a manifest audit, remove all explicitly disposable development artifacts, including useful-during-development items and tracked disposable scaffolding. Preserve source/product, secrets, retained dependencies and unclassified files.
- **/ProjectManifestAudit**: read-only LLM review of classifications, references and missing/unregistered files. Metadata validation is automated; whether a file is still needed requires project reasoning, not a filename heuristic.

The skill's short discovery metadata is registered; Pi's package installer and the bundled OpenCode installer also register the command stubs. Detailed instructions are separate references read on demand. The core skill suggests basic cleanup after meaningful completed-work checkpoints using a stable candidate fingerprint; it does not nag every turn or silently clean.

## Layout

New development debris belongs in `tmp`, `tmplogs`, `test-tools`, `scaffolding`, `tmpartifacts`; project-local external dependencies belong in `dependencies` when supported by their tooling. Existing source/assets/permanent tools remain in their established layout. Runtime dependencies are not disposable. See [the skill](skills/project-hygiene/SKILL.md).

## Install from this private GitHub repository

Requirements: Python 3.10+, Git, and an existing GitHub login with access to this private repository. Use your normal Git credential manager or SSH authentication; never paste tokens into these files or commands. The cleanup tool uses only the Python standard library. The recommended OpenCode installation additionally requires Node.js/npm (`npx`); Project Hygiene itself does not need to be published to npm.

### Pi / Pi-GUI

Pi supports Git packages directly. From a terminal:

```sh
pi install git:github.com/InsecurePassword/Project-Hygiene-Skill
pi list
```

This registers the one skill and three prompt templates from `package.json`. Add `--local` for a project-only installation. Restart/reload Pi; Pi-GUI must use the same Pi profile/configuration. Check `/ProjectClean`, `/ProjectDoneClean`, and `/ProjectManifestAudit` in command discovery before using them. Do not run cleanup just to test installation.

Updates and removal:

```sh
pi update --extensions
pi remove git:github.com/InsecurePassword/Project-Hygiene-Skill
```

`pi update --extensions` reconciles all installed extension packages, not just this one. For reproducibility, append `@<commit-sha>` to the Git source; pinned commits do not advance automatically. Removing this package does not delete project manifests or quarantined project files.

### OpenCode

The cross-agent [skills CLI](https://github.com/vercel-labs/skills) installs and wires skills directly into OpenCode. **Recommended:** run this from your project directory:

```sh
npx skills add InsecurePassword/Project-Hygiene-Skill/skills/project-hygiene --agent opencode
```

The source names the actual `skills/project-hygiene` directory inside this repository. Installation is project-local by default; add `--global` to make the skill available across projects. Restart/reload OpenCode and verify that `project-hygiene` is discovered.

This installs the skill with its bundled references and Python script. The separate `/ProjectClean`, `/ProjectDoneClean`, and `/ProjectManifestAudit` command templates under `.opencode/commands` are not registered by `skills add`. The alternative below installs the skill and those command templates together.

For Skills CLI-managed installations, update or remove the skill with:

```sh
npx skills update project-hygiene --project
npx skills remove project-hygiene --agent opencode
```

Run these from the same project directory. For a global installation, replace `--project` with `--global` on update and add `--global` on remove.

#### Bundled installer alternative: skill and slash commands

Use this as an alternative installation method, or to maintain an existing bundled-installer installation. It manages both the skill and command files. To switch the same destination to the Skills CLI, first use this installer's `uninstall` command with the original destination option; it moves both the skill and command files into its recovery backup. Preserve/reconcile any local edits it reports before retrying.

Clone using your existing Git authentication, then run the bundled installer:

```sh
git clone https://github.com/InsecurePassword/Project-Hygiene-Skill.git
cd Project-Hygiene-Skill
python scripts/install_opencode.py install
```

Default destination: `~/.config/opencode`. To install project-locally, pass `--config-dir "PATH/TO/PROJECT/.opencode"`. For a customized OpenCode config directory, pass that exact directory explicitly. On Windows use `py -3` instead of `python` if that is your installed Python launcher.

The installer copies only `skills/project-hygiene` and the three command templates. It refuses collisions with unowned files and refuses updates/removal of locally modified installed files. It does not modify OpenCode settings or other tools. Restart OpenCode and verify skill/command discovery; a real client smoke check remains necessary.

Update or remove with the same destination option originally used:

```sh
git pull --ff-only
python scripts/install_opencode.py update
python scripts/install_opencode.py uninstall
```

Updates and uninstall move previously installed package files into `.project-hygiene-install-backups/<id>` inside that config directory. This preserves recoverability but does not free their bytes. Unrelated files remain untouched. Review and remove obsolete backups manually when no longer needed.

The installer is deliberately small, not a transactional package manager. Stop clients while updating. Files are staged before replacement; ordinary caught errors roll back the previous installation while preserving failed new files. A process kill or additional failure during rollback can still leave a partial installation; inspect the printed recovery directory and its operation receipt before retrying. A stale installer lock requires confirming no installation process is active before removing it. Do not run concurrent install/update/uninstall operations.

### Loading and hooks

OpenCode discovers the installed skill through its `SKILL.md` metadata. Where installed, each compact command stub loads its own reference on demand. Project Hygiene installs no hooks, background watcher, automatic cleanup or inference service.

[Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) · [Pi prompt templates](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/prompt-templates.md) · [OpenCode commands](https://opencode.ai/docs/commands/) · [OpenCode skills](https://opencode.ai/docs/skills/)

## Manifest and Git

Initialization creates `.project-hygiene-<project-slug>-<UUID>.json` in the exact root. It binds the filename, UUID, root and Git directory. A copied/relocated manifest, multiple manifests, child-root selection or linked path fails closed. A deliberate move requires reinitialization/re-registration; portable policy and machine-specific state are not conflated.

Four categories: tracked, ignored-retained, disposable, deliverable. Category `tracked` is a preservation policy, not a command to add files to Git. Registration is exact-file based, never broad wildcard deletion. The CLI does not stage, commit, push, modify ignore rules, or infer cleanup permission from `.gitignore`. Final tracked-artifact removal appears as a working-tree deletion; review it before committing.

Ignore local manifests, `.project-hygiene-lock/` and `.project-hygiene-trash/` in each consumer project. Ignore temporary directories as appropriate, but retain secrets and useful local state. Never substitute blanket `git clean -X`/`-x` for this tool.

## Recovery and real disk space

Cleanup renames files into `.project-hygiene-trash/<project-id>/<batch-id>/files` on the same filesystem, with a durable receipt written first. Restore never intentionally overwrites existing files. No duplicate copy, compression, external upload or automatic permanent purge is performed.

**Quarantine is recoverable removal from the working tree, NOT space reclamation.** The report states bytes moved, not bytes freed. To reclaim storage the owner must review/purge selected quarantine batches through their OS later. No unlimited archival promise, automatic expiry or secret permanent deletion. Keep a compact result summary/build recipe when historical comparison matters; do not retain hundreds of gigabytes merely for hypothetical reuse.

Stop project writers before apply/restore. The Hygiene lock excludes other Hygiene processes, not arbitrary tools. The trusted, quiescent filesystem assumption is deliberate: this is not a security sandbox against malicious concurrent path replacement. Common secret filenames are protected as a backstop; unusual secret filenames must be categorized retained. Links/junctions and hard links are rejected or retained. Empty directories remain.

## Validation

Run `python -m unittest discover -s tests -v` from this repository. Tests use temporary fixture projects only. See [VALIDATION.md](VALIDATION.md) for actual evidence and limitations.

## Hooks

No hooks are installed. Start with explicit commands and core-skill checkpoint suggestions. An optional future Pi/OpenCode hook can call read-only status after meaningful work completion, but session idle/shutdown is not project completion and must never invoke final cleanup automatically.
