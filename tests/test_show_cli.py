import pytest

from src import show_v3


def test_read_ip_list_strips_empty_lines(tmp_path):
    ip_file = tmp_path / "ips.txt"
    ip_file.write_text("192.0.2.1\n\n198.51.100.5\n", encoding="utf-8")

    result = show_v3.read_ip_list(ip_file)

    assert result == ["192.0.2.1", "198.51.100.5"]


def test_read_commands_from_file(tmp_path):
    cmd_file = tmp_path / "cmds.txt"
    cmd_file.write_text("show version\n\nshow vlan brief\n", encoding="utf-8")

    result = show_v3.read_commands_from_file(cmd_file)

    assert result == ["show version", "show vlan brief"]


def test_prepare_output_dir_creates_nested(tmp_path, monkeypatch):
    outputs_dir = tmp_path / "outputs"
    monkeypatch.setattr(show_v3, "OUTPUTS_DIR", outputs_dir)

    created = show_v3.prepare_output_dir("nightly")

    assert created == outputs_dir / "nightly"
    assert created.exists()


def test_resolve_data_file_handles_relative_path(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(show_v3, "DATA_DIR", data_dir)

    nested = data_dir / "inputs"
    nested.mkdir()
    sample = nested / "ips.txt"
    sample.write_text("10.0.0.1\n", encoding="utf-8")

    resolved = show_v3.resolve_data_file("inputs/ips.txt", "IP list")

    assert resolved == sample


def test_resolve_data_file_raises_for_missing_relative(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(show_v3, "DATA_DIR", data_dir)

    with pytest.raises(FileNotFoundError):
        show_v3.resolve_data_file("inputs/missing.txt", "IP list")
