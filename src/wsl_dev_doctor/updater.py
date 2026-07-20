from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass

from wsl_dev_doctor.inventory import ToolInventory
from wsl_dev_doctor.registry import tool_by_id

Run = Callable[[tuple[str, ...]], tuple[int, str, str]]


@dataclass(frozen=True)
class SourceUpdater:
    source: str
    command: tuple[str, ...]
    scope: str


_NPM_PACKAGES = {
    "claude": "@anthropic-ai/claude-code",
    "codex": "@openai/codex",
}


def _source_updater(tool_id: str, path: str | None) -> SourceUpdater | None:
    """Return an updater only when a dedicated tool's source is recognizable."""
    if path is None:
        return None
    normalized = os.path.realpath(path).replace("\\", "/")
    npm_package = _NPM_PACKAGES.get(tool_id)
    if npm_package is not None and "/node_modules/" in normalized:
        return SourceUpdater(
            "npm global package", ("npm", "update", "--global", npm_package), "global_js"
        )
    if tool_id == "claude" and "/.local/share/claude/versions/" in normalized:
        return SourceUpdater("Claude standalone installer", ("claude", "update"), "dedicated")
    if tool_id == "codex" and (
        "/.codex/packages/standalone/" in normalized or "/.codex/releases/" in normalized
    ):
        return SourceUpdater("Codex standalone installer", ("codex", "update"), "dedicated")
    if tool_id == "uv" and normalized.endswith("/.local/bin/uv"):
        return SourceUpdater("uv standalone installer", ("uv", "self", "update"), "dedicated")
    return None


@dataclass(frozen=True)
class UpdatePlan:
    tool_id: str
    command: tuple[str, ...]
    status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _eligible(
    scope: str | None, include_system: bool, include_global_js: bool, include_homebrew: bool
) -> bool:
    return (
        scope == "dedicated"
        or (scope == "system" and include_system)
        or (scope == "global_js" and include_global_js)
        or (scope == "homebrew" and include_homebrew)
    )


def build_update_plan(
    inventory: Iterable[ToolInventory],
    selected_ids: Iterable[str],
    *,
    include_system: bool = False,
    include_global_js: bool = False,
    include_homebrew: bool = False,
) -> list[UpdatePlan]:
    by_id = {tool.id: tool for tool in inventory}
    plans: list[UpdatePlan] = []
    for tool_id in dict.fromkeys(selected_ids):
        spec = tool_by_id(tool_id)
        discovered = by_id.get(tool_id)
        source_updater: SourceUpdater | None = None
        if spec is None:
            plans.append(UpdatePlan(tool_id, (), "skipped", "Unknown registered tool."))
        elif discovered is None or discovered.status != "present":
            plans.append(UpdatePlan(tool_id, (), "skipped", "Tool is not present."))
        elif spec.update_command is None:
            plans.append(UpdatePlan(tool_id, (), "skipped", "No supported updater."))
        elif (
            spec.update_scope == "dedicated"
            and (source_updater := _source_updater(tool_id, discovered.path)) is None
        ):
            plans.append(
                UpdatePlan(
                    tool_id,
                    (),
                    "unsupported",
                    "Installation source could not be determined; no update was planned.",
                )
            )
        else:
            updater = source_updater if spec.update_scope == "dedicated" else None
            command = updater.command if updater is not None else spec.update_command
            scope = updater.scope if updater is not None else spec.update_scope
            source = updater.source if updater is not None else "registered package-manager updater"
            if not _eligible(scope, include_system, include_global_js, include_homebrew):
                plans.append(
                    UpdatePlan(
                        tool_id,
                        command,
                        "gated",
                        f"{source}; requires explicit opt-in for {scope} updates.",
                    )
                )
            else:
                plans.append(UpdatePlan(tool_id, command, "planned", f"Source: {source}."))
    return plans


def execute_update_plan(plans: Iterable[UpdatePlan], run: Run | None = None) -> list[UpdatePlan]:
    active_run = run or _run
    results: list[UpdatePlan] = []
    for plan in plans:
        if plan.status != "planned":
            results.append(plan)
            continue
        code, stdout, stderr = active_run(plan.command)
        detail = (stdout or stderr).strip()[:300]
        results.append(
            UpdatePlan(
                plan.tool_id,
                plan.command,
                "updated" if code == 0 else "failed",
                detail or f"Exit {code}.",
            )
        )
    return results


def _run(command: tuple[str, ...]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=300
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return 1, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def render_plan(plans: Iterable[UpdatePlan]) -> str:
    lines = ["# WSL Dev Doctor update plan", ""]
    for plan in plans:
        command = " ".join(plan.command) if plan.command else "—"
        lines.append(f"- **{plan.tool_id}**: `{plan.status}` — `{command}` — {plan.reason}")
    return "\n".join(lines) + "\n"
