import json
from pathlib import Path

import pytest

from devcheck.diagnostics import ConfigurationError, load_config, run_diagnostics


def config(**overrides):
    value = {
        "min_python": "3.10",
        "min_free_disk_mb": 100,
        "required_env": ["API_TOKEN"],
        "tools": ["git"],
    }
    value.update(overrides)
    return value


def test_success_report_is_healthy():
    report = run_diagnostics(
        config(),
        platform="test-platform",
        python_version=(3, 12, 1),
        path_lookup=lambda tool: f"/fake/{tool}",
        disk_usage=lambda path: type("Usage", (), {"free": 500 * 1024 * 1024})(),
        environ={"API_TOKEN": "present"},
    )
    assert report["status"] == "healthy"
    assert report["summary"]["failed"] == 0
    assert report["platform"] == "test-platform"


def test_missing_dependency_is_reported_as_failure():
    report = run_diagnostics(
        config(),
        python_version=(3, 12, 1),
        path_lookup=lambda tool: None,
        disk_usage=lambda path: type("Usage", (), {"free": 500 * 1024 * 1024})(),
        environ={},
    )
    assert report["status"] == "unhealthy"
    assert report["summary"]["failed"] == 2
    assert any(c["name"] == "developer_tool" and c["status"] == "fail"
               for c in report["checks"])


def test_malformed_configuration_is_rejected(tmp_path: Path):
    config_file = tmp_path / "broken.json"
    config_file.write_text('{"tools": [}', encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Malformed JSON"):
        load_config(str(config_file))


def test_configuration_root_must_be_object(tmp_path: Path):
    config_file = tmp_path / "array.json"
    config_file.write_text('["git"]', encoding="utf-8")
    with pytest.raises(ConfigurationError, match="JSON object"):
        load_config(str(config_file))


def test_report_is_json_serializable():
    report = run_diagnostics(
        config(required_env=[], tools=[]),
        python_version=(3, 12, 1),
        path_lookup=lambda tool: None,
        disk_usage=lambda path: type("Usage", (), {"free": 500 * 1024 * 1024})(),
        environ={},
    )
    assert json.loads(json.dumps(report))["schema_version"] == 1
