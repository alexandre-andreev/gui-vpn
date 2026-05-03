"""Integration tests for policy/awg-gui-helper (runs bash, no root needed).

AWG_TEST_MODE=1 overrides hardcoded paths and stubs out systemctl.
"""

import os
import subprocess
from pathlib import Path

HELPER = Path(__file__).parent.parent / "policy" / "awg-gui-helper"


def _run(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "AWG_TEST_MODE": "1", **(env_extra or {})}
    return subprocess.run(
        ["bash", str(HELPER), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _env(wg0: Path, original: Path | None = None) -> dict:
    return {
        "AWG_TEST_WG_CONF": str(wg0),
        "AWG_TEST_WG_ORIGINAL": str(original or wg0.parent / "wg0.conf.original"),
    }


# ── syntax ────────────────────────────────────────────────────────────────────


def test_helper_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(HELPER)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# ── systemctl subcommands ─────────────────────────────────────────────────────


def test_start_exits_zero():
    assert _run(["start"]).returncode == 0


def test_stop_exits_zero():
    assert _run(["stop"]).returncode == 0


def test_restart_exits_zero():
    assert _run(["restart"]).returncode == 0


def test_enable_exits_zero():
    assert _run(["enable"]).returncode == 0


def test_disable_exits_zero():
    assert _run(["disable"]).returncode == 0


def test_unknown_action_exits_nonzero():
    result = _run(["bogus-action"])
    assert result.returncode != 0
    assert "Usage:" in result.stderr


def test_no_action_exits_nonzero():
    result = _run([])
    assert result.returncode != 0


# ── apply-config ──────────────────────────────────────────────────────────────


def test_apply_config_replaces_wg0(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    wg0.write_text("old\n")
    new_conf = tmp_path / "New.conf"
    new_conf.write_text("new\n")

    result = _run(["apply-config", str(new_conf)], _env(wg0))

    assert result.returncode == 0
    assert wg0.read_text() == "new\n"


def test_apply_config_creates_backup_on_first_run(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("original content\n")
    new_conf = tmp_path / "New.conf"
    new_conf.write_text("new\n")

    _run(["apply-config", str(new_conf)], _env(wg0, original))

    assert original.read_text() == "original content\n"


def test_apply_config_does_not_overwrite_existing_backup(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("current\n")
    original.write_text("precious backup\n")
    new_conf = tmp_path / "New.conf"
    new_conf.write_text("new\n")

    _run(["apply-config", str(new_conf)], _env(wg0, original))

    assert original.read_text() == "precious backup\n"


def test_apply_config_leaves_no_tmp_file(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    wg0.write_text("old\n")
    new_conf = tmp_path / "New.conf"
    new_conf.write_text("new\n")

    _run(["apply-config", str(new_conf)], _env(wg0))

    assert not any(f.name.startswith("wg0.conf.tmp.") for f in tmp_path.iterdir())


def test_apply_config_missing_source_exits_nonzero(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    wg0.write_text("old\n")
    result = _run(["apply-config", str(tmp_path / "nonexistent.conf")], _env(wg0))
    assert result.returncode != 0
    assert "not a regular file" in result.stderr


def test_apply_config_no_arg_exits_nonzero(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    wg0.write_text("old\n")
    result = _run(["apply-config"], _env(wg0))
    assert result.returncode != 0


# ── restore-original ──────────────────────────────────────────────────────────


def test_restore_original_restores_from_backup(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    original = tmp_path / "wg0.conf.original"
    wg0.write_text("current\n")
    original.write_text("backup\n")

    result = _run(["restore-original"], _env(wg0, original))

    assert result.returncode == 0
    assert wg0.read_text() == "backup\n"


def test_restore_original_fails_when_no_backup(tmp_path):
    wg0 = tmp_path / "wg0.conf"
    wg0.write_text("current\n")
    original = tmp_path / "wg0.conf.original"

    result = _run(["restore-original"], _env(wg0, original))

    assert result.returncode != 0
    assert "backup not found" in result.stderr
