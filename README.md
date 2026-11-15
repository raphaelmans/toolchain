# Toolchain

An agent-friendly local toolchain audit and migration planner for macOS and Omarchy/Arch Linux. The catalog encodes the adopted [CLI Toolchain Standard](https://app.notion.com/p/4189439f148681599f1ceaaeb1b9f793), including owners, version prefixes and manual verification items. The Notion page remains the decision source; a public reader may not have access to it.

Requires Python 3.11+; no runtime dependencies. From a checkout:

```sh
python3 -m toolchain catalog
python3 -m toolchain audit
python3 -m toolchain audit --json
python3 -m toolchain select
```

Or install with `python3 -m pip install .` and use `toolchain` in place of `python3 -m toolchain`.

In the selector, move with arrows or j/k; space toggles an item, **g** toggles the current semantic group, **a** selects all, **n** clears all, and Enter prints a reviewable JSON plan. The selector starts with nothing selected. `catalog --json` exposes the platform-filtered catalog for agents. The plan contains argument arrays, existing paths, notes, prerequisites and verification steps. It never runs commands.

## Agent workflow

1. Run `audit --json`, inspect discovered paths and compare them with the catalog. PATH presence alone does not prove package ownership, version compliance or absence of other copies. Inspect package managers and `mise ls` as needed.
2. Ask the person to choose tools through `select`, or construct a plan from an explicit selection. Review the commands, platform, pin and notes. Install the package manager and mise 2026.11+ first; keep mise's release-age delay enabled.
3. Execute only approved, understood commands. The planner does not uninstall existing installations or change shell configuration: identify package ownership and dependencies first. Preserve system runtimes and services. Migrating PostgreSQL clusters requires a separate decision. Verify uncertain entries (treg and Defuddle) and Omarchy Neovim compatibility before installing.
4. Activate mise in the user's shell, then check `mise doctor`, `mise ls`, command paths and versions in interactive and non-interactive shells. Report unresolved ownership, duplicates and failures. Do not install pending, dropped or per-project tools from the reference as global tools.

`mise use --global` updates the existing global mise config; inspect it before execution. Claude and Grok require the reference's updater environment settings when managed by mise. Vendor applications are manual steps; they are not reinstalled automatically. On Linux, package commands target Arch/pacman and need adaptation on other distributions. Review every planned command, especially when select-all includes software already present.

## Development

```sh
python3 -m unittest discover -s tests
```

Audit results can contain local paths; review them before sharing. No telemetry is collected.
