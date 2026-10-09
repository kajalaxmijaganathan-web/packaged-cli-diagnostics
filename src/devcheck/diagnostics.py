"""Environment checks for DevCheck. Uses only the Python standard library."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when a diagnostics configuration file is invalid."""


def load_config(path: str | None) -> dict[str, Any]:
    """Load optional JSON configuration, or return safe defaults."""
    defaults: dict[str, Any] = {
        "min_python": "3.10",
        "min_free_disk_mb": 500,
        "required_env": [],
        "tools": ["git", "python", "pip"],
    }
    if path is None:
        return defaults

    config_path = Path(path)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"Cannot read config file '{path}': {exc}") from exc

    try:
        user_config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Malformed JSON in '{path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(user_config, dict):
        raise ConfigurationError("Configuration root must be a JSON object.")

    allowed = {"min_python", "min_free_disk_mb", "required_env", "tools"}
    unknown = sorted(set(user_config) - allowed)
    if unknown:
        raise ConfigurationError(f"Unknown configuration key(s): {', '.join(unknown)}")

    config = {**defaults, **user_config}
    if not isinstance(config["min_python"], str):
        raise ConfigurationError("'min_python' must be a string such as '3.10'.")
    try:
        tuple(int(part) for part in config["min_python"].split("."))
    except (ValueError, AttributeError) as exc:
        raise ConfigurationError("'min_python' must be a dotted version such as '3.10'.") from exc

    if not isinstance(config["min_free_disk_mb"], int) or config["min_free_disk_mb"] < 0:
        raise ConfigurationError("'min_free_disk_mb' must be a non-negative integer.")
    for key in ("required_env", "tools"):
        if not isinstance(config[key], list) or not all(
            isinstance(item, str) and item.strip() for item in config[key]
        ):
            raise ConfigurationError(f"'{key}' must be a list of non-empty strings.")
    return config


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def run_diagnostics(config: dict[str, Any], *, platform: str | None = None,
                    python_version: tuple[int, ...] | None = None,
                    path_lookup=shutil.which, disk_usage=shutil.disk_usage,
                    environ=None) -> dict[str, Any]:
    """Run checks and return stable, JSON-serializable results."""
    platform = platform or sys.platform
    python_version = python_version or sys.version_info[:3]
    environ = os.environ if environ is None else environ

    checks: list[dict[str, Any]] = []
    actual_version = ".".join(str(part) for part in python_version)
    min_version = _version_tuple(config["min_python"])
    actual_tuple = tuple(python_version)
    checks.append({
        "name": "python_version",
        "status": "pass" if actual_tuple >= min_version else "fail",
        "actual": actual_version,
        "required": config["min_python"],
        "message": "Python version meets requirement." if actual_tuple >= min_version
                   else f"Python {config['min_python']} or newer is required.",
    })

    root = Path.home().anchor or "/"
    try:
        usage = disk_usage(root)
        free_mb = usage.free // (1024 * 1024)
        disk_ok = free_mb >= config["min_free_disk_mb"]
        checks.append({
            "name": "disk_space",
            "status": "pass" if disk_ok else "fail",
            "actual_free_mb": free_mb,
            "required_free_mb": config["min_free_disk_mb"],
            "message": "Available disk space meets requirement." if disk_ok
                       else "Not enough free disk space.",
        })
    except OSError as exc:
        checks.append({
            "name": "disk_space", "status": "error",
            "message": f"Unable to inspect disk space: {exc}",
        })

    for variable in sorted(config["required_env"]):
        present = bool(environ.get(variable))
        checks.append({
            "name": "environment_variable",
            "variable": variable,
            "status": "pass" if present else "fail",
            "message": f"{variable} is set." if present else f"Required variable {variable} is missing.",
        })

    for tool in sorted(set(config["tools"])):
        location = path_lookup(tool)
        checks.append({
            "name": "developer_tool",
            "tool": tool,
            "status": "pass" if location else "fail",
            "path": location,
            "message": f"{tool} was found." if location else f"{tool} was not found on PATH.",
        })

    failed = sum(check["status"] == "fail" for check in checks)
    errors = sum(check["status"] == "error" for check in checks)
    return {
        "tool": "devcheck",
        "schema_version": 1,
        "platform": platform,
        "python": actual_version,
        "status": "unhealthy" if failed or errors else "healthy",
        "summary": {
            "total": len(checks),
            "passed": sum(check["status"] == "pass" for check in checks),
            "failed": failed,
            "errors": errors,
        },
        "checks": checks,
    }


def format_report(report: dict[str, Any]) -> str:
    """Format a human-readable report in a deterministic order."""
    lines = [
        "DevCheck — Developer Environment Health Report",
        f"Platform: {report['platform']}",
        f"Python:   {report['python']}",
        f"Status:   {report['status'].upper()}",
        "",
        "Checks:",
    ]
    for check in report["checks"]:
        status = check["status"].upper()
        lines.append(f"  [{status}] {check['message']}")
    summary = report["summary"]
    lines += [
        "",
        f"Summary: {summary['passed']} passed, {summary['failed']} failed, "
        f"{summary['errors']} errors ({summary['total']} total)",
    ]
    return "\n".join(lines)
