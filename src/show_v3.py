"""CLI helper that reads input files from /data and writes outputs to /outputs.

Example:
python show_v3.py --user admin --ip-file ip.txt --cmd-file show_switch.txt --output-dir bogay
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from getpass import getpass
from pathlib import Path
from threading import Lock

from netmiko import ConnectHandler

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"

print_lock = Lock()


def read_ip_list(file_path):
    with file_path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def read_manual_ips():
    print("Masukkan IP manual (satu per baris, ketik 'DONE' untuk selesai):")
    ip_list = []
    while True:
        line = input()
        if line.strip().upper() == "DONE":
            break
        if line.strip():
            ip_list.append(line.strip())
    return ip_list


def read_commands_from_file(file_path):
    with file_path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def resolve_data_file(path_value, description):
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = DATA_DIR / candidate
    if not candidate.is_file():
        raise FileNotFoundError(f"{description} file not found: {candidate}")
    return candidate


def prepare_output_dir(subdir):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS_DIR if not subdir else OUTPUTS_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


def connect_and_run_single(ip, username, password, enable, commands, combine_output, output_dir):
    result = {"ip": ip, "success": True, "output": "", "error": ""}
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
            fragments = []

            for cmd in commands:
                output = ssh.send_command_timing(cmd, read_timeout=300, delay_factor=2)
                fragments.append(f"\n=== {hostname} ({ip}) - {cmd} ===\n{output}\n")

            result["hostname"] = hostname
            result["output"] = "".join(fragments)

            if combine_output:
                with print_lock:
                    print(result["output"])
            else:
                filename = output_dir / f"{hostname}_{ip.replace('.', '_')}.txt"
                with filename.open("w", encoding="utf-8") as handle:
                    handle.write(result["output"])
                with print_lock:
                    print(f"[INFO] Output saved: {filename}")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        result["success"] = False
        result["error"] = f"[ERROR] {ip}: {exc}"
        with print_lock:
            print(result["error"])
    return result


def connect_and_run(ip_list, username, password, enable, commands, combine_output, output_dir, max_threads):
    output_dir.mkdir(parents=True, exist_ok=True)
    error_log = []
    failed_ips = []

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
        print(f"[INFO] Errors logged in: {err_path}")

    if failed_ips:
        failed_path = output_dir / "failed_ips.txt"
        with failed_path.open("w", encoding="utf-8") as handle:
            for ip in failed_ips:
                handle.write(ip + "\n")
        print(f"[INFO] Failed IPs saved in: {failed_path}")


def main():
    parser = argparse.ArgumentParser(description="Netmiko CLI Tool for Cisco Devices (Multithreaded, data/outputs aware)")
    parser.add_argument("--user", required=True, help="Username for device login")
    parser.add_argument("--ip-file", help="Filename under /data containing list of IPs")
    parser.add_argument("--manual", action="store_true", help="Input IPs manually via prompt")
    parser.add_argument("--cmds", help="Comma-separated list of commands")
    parser.add_argument("--cmd-file", help="Filename under /data containing commands")
    parser.add_argument("--output-dir", help="Optional subdirectory inside /outputs for results")
    parser.add_argument("--combine", action="store_true", help="Combine all output into one file")
    parser.add_argument("--threads", type=int, default=5, help="Maximum number of concurrent threads (default=5)")

    args = parser.parse_args()

    if not args.ip_file and not args.manual:
        print("[ERROR] Anda harus memilih --ip-file atau --manual.")
        sys.exit(1)

    if not args.cmds and not args.cmd_file:
        print("[ERROR] Anda harus memberikan --cmds atau --cmd-file.")
        sys.exit(1)

    if args.cmd_file:
        try:
            cmd_path = resolve_data_file(args.cmd_file, "Command")
            commands = read_commands_from_file(cmd_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Gagal membaca file command: {exc}")
            sys.exit(1)
    else:
        commands = [cmd.strip() for cmd in args.cmds.split(",") if cmd.strip()]

    password = getpass("Password: ")
    enable = getpass("Enable Password: ")

    if args.ip_file:
        try:
            ip_path = resolve_data_file(args.ip_file, "IP list")
            ip_list = read_ip_list(ip_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Gagal membaca file IP: {exc}")
            sys.exit(1)
    else:
        ip_list = read_manual_ips()

    original_count = len(ip_list)
    ip_list = list(dict.fromkeys(ip_list))
    deduped_count = len(ip_list)
    if deduped_count < original_count:
        print(f"[INFO] Duplikat terdeteksi. {original_count - deduped_count} IP di-skip.")

    output_dir = prepare_output_dir(args.output_dir)

    connect_and_run(ip_list, args.user, password, enable, commands, args.combine, output_dir, args.threads)


if __name__ == "__main__":
    main()
