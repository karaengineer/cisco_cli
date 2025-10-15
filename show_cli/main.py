"""CLI helper that reads input files from /data and writes outputs to /outputs.

Examples:
python -m show_cli.main --user admin --ip-file data/inputs/ip_sample.txt --cmd-file data/inputs/show_sample.txt --output-dir demo
show-cli --user admin --ip-file data/inputs/ip_sample.txt --cmd-file data/inputs/show_sample.txt --output-dir demo
"""

import argparse
import configparser
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from getpass import getpass
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from netmiko import ConnectHandler

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"
LOGGER = logging.getLogger("show_cli")
output_lock = Lock()

TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}
CONFIG_SECTION = "cli"


def read_ip_list(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def read_manual_ips() -> list[str]:
    LOGGER.info("Masukkan IP manual (satu per baris, ketik 'DONE' untuk selesai):")
    ip_list: list[str] = []
    while True:
        line = input()
        if line.strip().upper() == "DONE":
            break
        if line.strip():
            ip_list.append(line.strip())
    return ip_list


def read_commands_from_file(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def resolve_data_file(path_value: str | Path, description: str) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = DATA_DIR / candidate
    if not candidate.is_file():
        raise FileNotFoundError(f"{description} file not found: {candidate}")
    return candidate


def prepare_output_dir(subdir: str | None) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS_DIR if not subdir else OUTPUTS_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        raise ValueError("Boolean value cannot be None")
    candidate = str(value).strip().lower()
    if candidate in TRUE_VALUES:
        return True
    if candidate in FALSE_VALUES:
        return False
    raise ValueError(f"Tidak dapat mengonversi '{value}' menjadi boolean.")


def load_config(config_path: Path) -> Dict[str, str]:
    candidate = Path(config_path)
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    if not candidate.is_file():
        raise FileNotFoundError(f"Config file not found: {candidate}")

    parser = configparser.ConfigParser()
    parser.read(candidate, encoding="utf-8")

    if parser.has_section(CONFIG_SECTION):
        data = dict(parser[CONFIG_SECTION])
    else:
        data = dict(parser.defaults())

    if not data:
        raise ValueError(f"Config file {candidate} does not contain section [{CONFIG_SECTION}] or defaults.")

    return {key.strip(): value for key, value in data.items()}


def merge_args_with_config(args: argparse.Namespace, config: Dict[str, str]) -> argparse.Namespace:
    if not config:
        return args

    namespace = vars(args).copy()
    casters: Dict[str, Any] = {
        "combine": parse_bool,
        "manual": parse_bool,
        "threads": int,
        "log_level": str,
    }
    nullable_fields = {"user", "ip_file", "cmds", "cmd_file", "output_dir"}

    for key, value in config.items():
        attr = key.replace("-", "_")
        if attr == "config" or attr not in namespace:
            continue
        if namespace[attr] is not None:
            continue

        sanitized: Any = value
        if isinstance(value, str):
            sanitized = value.strip()
            if attr in nullable_fields and sanitized == "":
                continue

        caster = casters.get(attr, str)
        try:
            namespace[attr] = caster(sanitized)
        except ValueError as exc:
            raise ValueError(f"Konfigurasi tidak valid untuk '{attr}': {value}") from exc

    return argparse.Namespace(**namespace)


def connect_and_run_single(
    ip: str,
    username: str,
    password: str,
    enable: str,
    commands: list[str],
    combine_output: bool,
    output_dir: Path,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ip": ip, "success": True, "output": "", "error": ""}
    try:
        device = {
            "device_type": "cisco_ios",
            "host": ip,
            "username": username,
            "password": password,
            "secret": enable,
        }
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            hostname = ssh.find_prompt().strip("#")
            fragments: list[str] = []

            for cmd in commands:
                output = ssh.send_command_timing(cmd, read_timeout=300, delay_factor=2)
                fragments.append(f"\n=== {hostname} ({ip}) - {cmd} ===\n{output}\n")

            result["hostname"] = hostname
            result["output"] = "".join(fragments)

            if combine_output:
                with output_lock:
                    print(result["output"], end="")
            else:
                filename = output_dir / f"{hostname}_{ip.replace('.', '_')}.txt"
                with filename.open("w", encoding="utf-8") as handle:
                    handle.write(result["output"])
                LOGGER.info("Output saved: %s", filename)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        result["success"] = False
        result["error"] = f"{ip}: {exc}"
        LOGGER.error("Gagal memproses %s: %s", ip, exc)
    return result


def connect_and_run(
    ip_list: list[str],
    username: str,
    password: str,
    enable: str,
    commands: list[str],
    combine_output: bool,
    output_dir: Path,
    max_threads: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    error_log: list[str] = []
    failed_ips: list[str] = []

    if combine_output:
        combined_path = output_dir / "combined_output.txt"
        with combined_path.open("w", encoding="utf-8") as combined_file:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(connect_and_run_single, ip, username, password, enable, commands, True, output_dir)
                    for ip in ip_list
                ]
                for future in as_completed(futures):
                    result = future.result()
                    if result["success"]:
                        combined_file.write(result["output"])
                    else:
                        error_log.append(result["error"])
                        failed_ips.append(result["ip"])
    else:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(connect_and_run_single, ip, username, password, enable, commands, False, output_dir)
                for ip in ip_list
            ]
            for future in as_completed(futures):
                result = future.result()
                if not result["success"]:
                    error_log.append(result["error"])
                    failed_ips.append(result["ip"])

    if error_log:
        err_path = output_dir / "connection_errors.txt"
        with err_path.open("w", encoding="utf-8") as handle:
            for line in error_log:
                handle.write(line + "\n")
        LOGGER.info("Errors logged in: %s", err_path)

    if failed_ips:
        failed_path = output_dir / "failed_ips.txt"
        with failed_path.open("w", encoding="utf-8") as handle:
            for ip in failed_ips:
                handle.write(ip + "\n")
        LOGGER.info("Failed IPs saved in: %s", failed_path)


def configure_logging(level: str) -> None:
    level_name = (level or "INFO").upper()
    numeric_level = logging.getLevelName(level_name)
    if isinstance(numeric_level, str):
        numeric_level = logging.INFO
        logging.basicConfig(level=numeric_level, format="%(asctime)s [%(levelname)s] %(message)s", force=True)
        LOGGER.warning("Log level %s tidak dikenal, menggunakan INFO sebagai bawaan.", level)
    else:
        logging.basicConfig(level=numeric_level, format="%(asctime)s [%(levelname)s] %(message)s", force=True)
        LOGGER.debug("Logging configured at %s", level_name)
    logging.getLogger().setLevel(numeric_level)
    LOGGER.setLevel(numeric_level)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Netmiko CLI Tool for Cisco Devices (Multithreaded, data/outputs aware)",
    )
    parser.add_argument("--config", help="Path to INI configuration file (section [cli]).")
    parser.add_argument("--user", help="Username for device login", default=None)
    parser.add_argument("--ip-file", help="Filename under /data containing list of IPs", default=None)
    parser.add_argument("--manual", action="store_true", default=None, help="Input IPs manually via prompt")
    parser.add_argument("--cmds", help="Comma-separated list of commands", default=None)
    parser.add_argument("--cmd-file", help="Filename under /data containing commands", default=None)
    parser.add_argument("--output-dir", help="Optional subdirectory inside /outputs for results", default=None)
    parser.add_argument("--combine", action="store_true", default=None, help="Combine all output into one file")
    parser.add_argument("--threads", type=int, default=None, help="Maximum number of concurrent threads")
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    args = parser.parse_args()

    # Configure provisional logging so config loading errors are surfaced.
    configure_logging(args.log_level or "INFO")

    config_values: Dict[str, str] = {}
    if args.config:
        try:
            config_values = load_config(Path(args.config))
            LOGGER.debug("Config values loaded: %s", config_values)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.error("Gagal memuat file konfigurasi %s: %s", args.config, exc)
            sys.exit(1)

    try:
        args = merge_args_with_config(args, config_values)
    except ValueError as exc:
        LOGGER.error("%s", exc)
        sys.exit(1)

    if args.log_level is None and "log_level" in config_values:
        args.log_level = config_values["log_level"]
    configure_logging(args.log_level or "INFO")

    if args.user is None:
        LOGGER.error("Parameter user wajib diisi (argumen --user atau konfigurasi).")
        sys.exit(1)

    manual_mode = args.manual if args.manual is not None else False
    combine_output = args.combine if args.combine is not None else False
    threads = args.threads if args.threads is not None else int(config_values.get("threads", 5))

    if args.ip_file is None and not manual_mode:
        LOGGER.error("Anda harus memilih --ip-file atau --manual.")
        sys.exit(1)

    if args.cmds is None and args.cmd_file is None:
        LOGGER.error("Anda harus memberikan --cmds atau --cmd-file.")
        sys.exit(1)

    if args.cmd_file:
        try:
            cmd_path = resolve_data_file(args.cmd_file, "Command")
            commands = read_commands_from_file(cmd_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.error("Gagal membaca file command: %s", exc)
            sys.exit(1)
    else:
        commands = [cmd.strip() for cmd in (args.cmds or "").split(",") if cmd.strip()]

    password = getpass("Password: ")
    enable = getpass("Enable Password: ")

    if args.ip_file:
        try:
            ip_path = resolve_data_file(args.ip_file, "IP list")
            ip_list = read_ip_list(ip_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.error("Gagal membaca file IP: %s", exc)
            sys.exit(1)
    else:
        ip_list = read_manual_ips()

    original_count = len(ip_list)
    ip_list = list(dict.fromkeys(ip_list))
    deduped_count = len(ip_list)
    if deduped_count < original_count:
        LOGGER.info("Duplikat terdeteksi. %s IP di-skip.", original_count - deduped_count)

    output_dir = prepare_output_dir(args.output_dir)

    LOGGER.info(
        "Menjalankan perintah ke %s perangkat dengan %s thread (combine_output=%s).",
        len(ip_list),
        threads,
        combine_output,
    )

    connect_and_run(ip_list, args.user, password, enable, commands, combine_output, output_dir, threads)


if __name__ == "__main__":
    main()
