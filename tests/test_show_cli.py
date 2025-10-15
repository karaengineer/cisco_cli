import argparse

import pytest

from show_cli import main as cli


def test_read_ip_list_strips_empty_lines(tmp_path):
    ip_file = tmp_path / "ips.txt"
    ip_file.write_text("192.0.2.1\n\n198.51.100.5\n", encoding="utf-8")

    result = cli.read_ip_list(ip_file)

    assert result == ["192.0.2.1", "198.51.100.5"]


def test_read_commands_from_file(tmp_path):
    cmd_file = tmp_path / "cmds.txt"
    cmd_file.write_text("show version\n\nshow vlan brief\n", encoding="utf-8")

    result = cli.read_commands_from_file(cmd_file)

    assert result == ["show version", "show vlan brief"]


def test_prepare_output_dir_creates_nested(tmp_path, monkeypatch):
    outputs_dir = tmp_path / "outputs"
    monkeypatch.setattr(cli, "OUTPUTS_DIR", outputs_dir)

    created = cli.prepare_output_dir("nightly")

    assert created == outputs_dir / "nightly"
    assert created.exists()


def test_resolve_data_file_handles_relative_path(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)

    nested = data_dir / "inputs"
    nested.mkdir()
    sample = nested / "ips.txt"
    sample.write_text("10.0.0.1\n", encoding="utf-8")

    resolved = cli.resolve_data_file("inputs/ips.txt", "IP list")

    assert resolved == sample


def test_resolve_data_file_raises_for_missing_relative(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)

    with pytest.raises(FileNotFoundError):
        cli.resolve_data_file("inputs/missing.txt", "IP list")


def test_merge_args_with_config_applies_defaults():
    args = argparse.Namespace(
        config=None,
        user=None,
        ip_file=None,
        manual=None,
        cmds=None,
        cmd_file=None,
        output_dir=None,
        combine=None,
        threads=None,
        log_level=None,
    )
    config = {"user": "admin", "ip_file": "inputs/ip_sample.txt", "threads": "3", "combine": "true"}

    merged = cli.merge_args_with_config(args, config)

    assert merged.user == "admin"
    assert merged.ip_file == "inputs/ip_sample.txt"
    assert merged.threads == 3
    assert merged.combine is True


def test_load_config_reads_cli_section(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        "[cli]\nuser = admin\nthreads = 7\ncombine = false\n",
        encoding="utf-8",
    )

    data = cli.load_config(config_file)

    assert data["user"] == "admin"
    assert data["threads"] == "7"
    assert data["combine"] == "false"
