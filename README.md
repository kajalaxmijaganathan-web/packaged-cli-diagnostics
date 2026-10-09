# DevCheck CLI

DevCheck is a small, installable Python command-line tool that checks whether a machine is ready for development. It reports Python version, available disk space, required environment variables, and configured developer tools.

## Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux
- No runtime third-party dependencies

## Install locally (Windows PowerShell)

Open a terminal in the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

If PowerShell blocks activation, you can run the environment's Python directly:
`.venv\Scripts\python.exe -m pip install -e .`

## Usage

```powershell
devcheck
devcheck --json
devcheck --config examples/diagnostics.json
devcheck --json --config examples/diagnostics.json
```

If the `devcheck` command is not found immediately, try:
`python -m devcheck.cli` (from the source project) or reopen the terminal after installation.

## Configuration

Configuration is optional JSON. Supported keys:

| Key | Type | Default | Meaning |
|---|---|---|---|
| `min_python` | string | `"3.10"` | Minimum acceptable Python version |
| `min_free_disk_mb` | integer | `500` | Minimum free disk space in MiB |
| `required_env` | array of strings | `[]` | Environment variables that must be set |
| `tools` | array of strings | `["git", "python", "pip"]` | Executables to locate on `PATH` |

Unknown keys, malformed JSON, unreadable files, and invalid field types are rejected. The tool checks only whether a required variable is set; it never prints secret values.

## Exit codes

- `0`: all checks passed
- `1`: one or more environment checks failed
- `2`: invalid/unreadable configuration

This makes DevCheck usable in scripts and CI pipelines.

## Run tests

```powershell
python -m pytest -v
```

Tests cover a healthy environment, missing environment/tool dependencies, malformed JSON, and JSON-serializable reports. System-dependent checks are injected in tests so results are repeatable.

## Project layout

```text
packaged-cli-diagnostics/
├── pyproject.toml
├── README.md
├── src/
│   └── devcheck/
│       ├── __init__.py
│       ├── cli.py
│       └── diagnostics.py
├── tests/
│   └── test_diagnostics.py
└── examples/
    ├── diagnostics.json
    └── sample-report.json
```

## Notes

- JSON output uses sorted keys and a stable schema version.
- Environment variable values are not included in reports.
- Disk space is checked on the system drive/root.
- The sample report is illustrative, not a report from your machine.
