# Usage Guide

## Prerequisites
- Python 3.10 or newer.
- Network reachability to the target devices.
- Credentials with privilege access (enable mode).

Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# alternatively install the editable package (includes dev dependencies)
pip install -e .[dev]
```

## Preparing Data
- Duplicate `data/templates/ip_template.txt` and fill with your device IPs.
- Duplicate `data/templates/cmd_template.txt` and list CLI commands, one per line.
- Place raw or confidential files under `data/raw/` if you prefer to keep them outside version control.

Sample, commit-friendly files live in `data/inputs/` for quick demonstrations.

## Running the Tool

```bash
show-cli --user <username> ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir nightly-run --threads 10
```

Alternative: provide inline commands instead of a file.

```bash
python -m show_cli.main --user <username> ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmds "show version,show ip interface brief" ^
    --output-dir nightly-run --combine
```

The CLI prompts for `Password` and `Enable Password`, then spawns concurrent Netmiko sessions. Outputs appear under `outputs/<chosen-dir>`, alongside `connection_errors.txt` and `failed_ips.txt` if problems occurred.

Adjust verbosity with `--log-level` (e.g., `--log-level DEBUG`) when troubleshooting.

## Using a Config File

Create an INI file (defaults section `[cli]`) to pre-fill arguments:

```ini
[cli]
user = admin
ip_file = inputs/ip_sample.txt
cmd_file = inputs/show_sample.txt
threads = 8
combine = true
log_level = INFO
command_timeout = 300
delay_factor = 2.0
session_timeout = 30
```

Then run:

```bash
show-cli --config data/templates/config_template.ini
```

CLI arguments override values from the config file when provided.
If the configuration file sits inside `data/`, you can simply reference it by filename:

```bash
show-cli --config config.ini
```

Adjust `command_timeout`, `delay_factor`, or `session_timeout` when devices need more time to respond.

## Testing
```bash
pytest
```
The suite validates helper utilities like file readers and output directory creation. Extend it when new functionality is added (e.g., parsing logic or custom logging).

## Tips
- Adjust `--threads` to match your environment capacity; avoid overwhelming network equipment.
- Keep `outputs/` clean by deleting folders from previous runs after collecting artifacts.
