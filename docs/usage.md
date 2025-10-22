# Usage Guide

This document complements the top-level README with step-by-step instructions and extra context for day-to-day operation.

## 1. Prerequisites
- Python 3.10 or newer.
- Network reachability to each target device.
- Device credentials with enable/privileged access.
- Optional: configuration file under `data/` (for repeatable runs).

## 2. Installation
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
pip install -e .[dev]           # needed for testing and console script
```

## 3. Preparing Data
1. Copy `data/templates/ip_template.txt` -> `data/inputs/ip_sample.txt` (or similar) and populate it with one IP per line.
2. Copy `data/templates/cmd_template.txt` -> `data/inputs/show_sample.txt` and list each CLI command on its own line.
3. For confidential or bulky files, place them under `data/raw/` (ignored by Git). Keep small, shareable samples in `data/inputs/` so other contributors can reproduce behaviour.

## 4. Running the CLI

### 4.1 Explicit arguments
```powershell
show-cli --user <username> `
    --ip-file data/inputs/ip_sample.txt `
    --cmd-file data/inputs/show_sample.txt `
    --output-dir nightly-run `
    --threads 10
```

```bash
show-cli --user <username> \
  --ip-file data/inputs/ip_sample.txt \
  --cmd-file data/inputs/show_sample.txt \
  --output-dir nightly-run \
  --threads 10
```

To send inline commands without a file:
```powershell
python -m show_cli.main --user <username> `
    --ip-file data/inputs/ip_sample.txt `
    --cmds "show version,show ip interface brief" `
    --output-dir nightly-run --combine
```

You will be prompted for `Password` and `Enable Password`. Outputs are placed under `outputs/<chosen-dir>` along with `connection_errors.txt` and `failed_ips.txt` when issues arise. Use `--log-level DEBUG` for verbose logging during troubleshooting.

### 4.2 Configuration file
```ini
[cli]
user = admin
# password = your-device-password
# enable_password = your-enable-password
ip_file = inputs/ip_sample.txt
cmd_file = inputs/show_sample.txt
threads = 8
combine = true
log_level = INFO
command_timeout = 300
delay_factor = 2.0
session_timeout = 30
```

Save as `data/config.ini` (or another path). Run the CLI with:
```bash
show-cli --config config.ini
```

The loader searches both the project root and the `data/` directory, so `--config config.ini` works for `data/config.ini`. Any CLI flags supplied alongside `--config` override the corresponding values from the file. Only store `password` or `enable_password` here if you can protect the file; the values are plain text.

## 5. Output Structure
- Per-device text files under `outputs/<dir>/` (unless `--combine` is enabled).
- `combined_output.txt` when `--combine` is used.
- `connection_errors.txt` containing the error messages.
- `failed_ips.txt` listing devices that could not be reached or executed.

## 6. Testing
```bash
python -m pytest
```
The current suite focuses on helper utilities (file readers, path resolution, and configuration parsing). Extend it with Netmiko mocks or integration flows as new features are added.

## 7. Operational Tips
- Increase `--threads` gradually to avoid overwhelming your network hardware.
- Adjust `command_timeout`, `delay_factor`, or `session_timeout` for slow or heavily loaded devices.
- Periodically clear old folders under `outputs/` to keep runs organised.
