# WSL Dev Environment Doctor

[![CI](https://github.com/rriordan/wsl-dev-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/rriordan/wsl-dev-doctor/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/rriordan/wsl-dev-doctor?display_name=tag)](https://github.com/rriordan/wsl-dev-doctor/releases/latest)

A safe, read-only CLI that turns common WSL/Linux developer-environment failures into a concise Markdown or JSON diagnostic report.

It checks WSL detection, essential tooling, stale `PATH` entries, disk pressure, Docker daemon availability, listening TCP ports, and NVIDIA GPU visibility. It inventories environment-variable **names only**—never values.

## Why it exists

Diagnosing a development environment often means stitching together shell commands, half-remembered setup steps, and error messages. This tool provides a repeatable baseline report with prioritized, actionable remediation without changing the host.

## Features

- WSL-aware platform detection
- Comprehensive categorized inventory of 60+ package, runtime, AI coding, cloud, container, build, and editor CLIs
- Missing `PATH` directory detection
- Root filesystem capacity check
- Docker daemon connectivity check
- Listening TCP-port inventory
- NVIDIA GPU visibility check through `nvidia-smi`
- Environment-variable name inventory with secret-like names counted but never exposed as values
- Markdown and JSON output
- Exit thresholds for CI or shell automation
- Safe updater planning with dry-run default, built-in/custom presets, and an interactive terminal selector

## Demo

![Terminal demo of a representative WSL Dev Environment Doctor report](docs/demo-terminal.svg)

The illustration is based on a real local run. It shows why the tool is useful:
it distinguishes healthy components from actionable warnings, then offers the
next remediation steps without changing the environment.

## Quick start

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rriordan/wsl-dev-doctor.git
cd wsl-dev-doctor
uv sync --all-groups
uv run wsl-doctor --format markdown --output wsl-doctor-report.md
```

Print a JSON report instead:

```bash
uv run wsl-doctor --format json --output -
```

Fail a script if a warning or failure is present:

```bash
uv run wsl-doctor --fail-on warn --output -
```

## Tool inventory

The report inventories a broad registry of developer tools. Each item is
`present` or `not_present`; absence is a factual result, not a warning. When a
tool is detected, the report includes its best-effort version and whether this
release supports updating it.

## Updates and presets

Updates are dry-run by default and only execute when both `--apply` and `--yes`
are supplied. Review the proposed commands first:

```bash
# Plan updates for all detected tools with a supported updater; nothing is changed.
uv run wsl-doctor update --dry-run

# Choose detected, updateable tools with arrow keys and spacebar.
uv run wsl-doctor update --interactive

# Plan an AI coding environment update.
uv run wsl-doctor update --preset ai-dev

# Save and use a custom preset containing known registry IDs.
uv run wsl-doctor preset save my-stack --tool claude --tool codex --tool uv
uv run wsl-doctor update --preset my-stack
```

Dedicated updaters are selected only after the tool's installation source is
recognized. For example, a standalone Codex installation uses `codex update`,
while an npm-installed Codex is routed to npm's global updater and remains
gated. Unknown sources are reported as unsupported rather than guessed.

Broad package-manager updates remain gated and require an explicit flag:
`--include-system-packages`, `--include-global-js-packages`, or
`--include-homebrew`. For example, after reviewing the dry-run plan:

```bash
uv run wsl-doctor update --tool pnpm --include-global-js-packages --apply --yes
```

Custom presets are stored at `~/.config/wsl-dev-doctor/presets.toml`. They can
select only registered tool IDs; arbitrary shell commands are intentionally not
supported.

## Example output

See [`examples/sample-report.md`](examples/sample-report.md).

## Release notes

The first release, [`v0.1.0`](https://github.com/rriordan/wsl-dev-doctor/releases/tag/v0.1.0), is available now. Its full notes are in [`docs/releases/v0.1.0.md`](docs/releases/v0.1.0.md).

## How it works

The CLI gathers a small, explicit set of local signals using standard tools such as `ss`, `docker`, and `nvidia-smi`. Each diagnostic produces a status, evidence suitable for structured output, and remediation where action is warranted. The report renderer keeps those signals usable by humans and automation alike.

## Tests

```bash
make check
make test
```

## Roadmap

- Windows-host companion checks through `wsl.exe --status`
- Opt-in redacted support bundles with a review preview
- Recorded fixtures for WSL1, WSL2, Docker Desktop, and Docker Engine scenarios
- GitHub Releases and CI status are published above

## Limitations

- It performs Linux-side checks only; it cannot fully diagnose Windows host settings from inside WSL.
- Docker and GPU results depend on their respective CLIs being installed and accessible.
- Port inspection is limited to TCP listeners available through `ss`.
- It gives remediation guidance but never applies changes.

## Security and privacy

The tool is intentionally read-only. It does not read shell history, `.env` files, credentials, or configuration files. It does not print environment-variable values. Review reports before sharing because ordinary version and system details can still be operationally sensitive. See [`SECURITY.md`](SECURITY.md).

## AI-assisted development note

This project was built with AI-assisted development and human review. It emphasizes a narrow scope, deterministic checks, testability, and transparent limitations rather than claims of production readiness.
