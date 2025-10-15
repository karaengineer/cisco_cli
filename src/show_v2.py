# This script is designed to be run from the command line.
# Example usage:
# python show_v2.py --user admin --ip-file ip.txt --cmds "show version,show ip interface brief" --output-dir output_show --combine --threads 5

import os
import sys
import argparse
from netmiko import ConnectHandler
from getpass import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pathlib import Path

print_lock = Lock()

def read_ip_list(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

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
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

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
            all_output = []

            for cmd in commands:
                output = ssh.send_command_timing(cmd, read_timeout=300, delay_factor=2)
                formatted = f"\n=== {hostname} ({ip}) - {cmd} ===\n{output}\n"
                all_output.append(formatted)

            result["hostname"] = hostname
            result["output"] = "".join(all_output)

            if combine_output:
                with print_lock:
                    print(result["output"])
            else:
                filename = os.path.join(output_dir, f"{hostname}_{ip.replace('.', '_')}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(result["output"])
                with print_lock:
                    print(f"[INFO] Output saved: {filename}")
    except Exception as e:
        result["success"] = False
        result["error"] = f"[ERROR] {ip}: {e}"
        with print_lock:
            print(result["error"])
    return result

def connect_and_run(ip_list, username, password, enable, commands, combine_output, output_dir, max_threads):
    os.makedirs(output_dir, exist_ok=True)
    error_log = []
    failed_ips = []

    if combine_output:
        combined_path = os.path.join(output_dir, "combined_output.txt")
        with open(combined_path, "w", encoding="utf-8") as combined_file:
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

    # Simpan error log
    if error_log:
        err_path = os.path.join(output_dir, "connection_errors.txt")
        with open(err_path, "w", encoding="utf-8") as f:
            for line in error_log:
                f.write(line + "\n")
        print(f"[INFO] Errors logged in: {err_path}")

    # Simpan IP gagal
    if failed_ips:
        failed_path = os.path.join(output_dir, "failed_ips.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            for ip in failed_ips:
                f.write(ip + "\n")
        print(f"[INFO] Failed IPs saved in: {failed_path}")

def main():
    parser = argparse.ArgumentParser(description="Netmiko CLI Tool for Cisco Devices (Multithreaded)")
    parser.add_argument("--user", required=True, help="Username for device login")
    parser.add_argument("--ip-file", help="File path containing list of IPs")
    parser.add_argument("--manual", action="store_true", help="Input IPs manually via prompt")
    parser.add_argument("--cmds", help="Comma-separated list of commands")
    parser.add_argument("--cmd-file", help="File path containing one command per line")
    parser.add_argument("--output-dir", default="output_show", help="Directory to save outputs")
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
            commands = read_commands_from_file(args.cmd_file)
        except Exception as e:
            print(f"[ERROR] Gagal membaca file command: {e}")
            sys.exit(1)
    else:
        commands = [cmd.strip() for cmd in args.cmds.split(",") if cmd.strip()]

    password = getpass("Password: ")
    enable = getpass("Enable Password: ")

    if args.ip_file:
        try:
            ip_list = read_ip_list(args.ip_file)
        except Exception as e:
            print(f"[ERROR] Gagal membaca file IP: {e}")
            sys.exit(1)
    else:
        ip_list = read_manual_ips()

    # Deduplicate IPs (keep order)
    original_count = len(ip_list)
    ip_list = list(dict.fromkeys(ip_list))
    deduped_count = len(ip_list)
    if deduped_count < original_count:
        print(f"[INFO] Duplikat terdeteksi. {original_count - deduped_count} IP di-skip.")

    connect_and_run(ip_list, args.user, password, enable, commands, args.combine, args.output_dir, args.threads)

if __name__ == "__main__":
    main()
