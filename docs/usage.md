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
```

## Preparing Data
- Duplicate `data/templates/ip_template.txt` and fill with your device IPs.
- Duplicate `data/templates/cmd_template.txt` and list CLI commands, one per line.
- Place raw or confidential files under `data/raw/` if you prefer to keep them outside version control.

Sample, commit-friendly files live in `data/inputs/` for quick demonstrations.

## Running the Tool

### show_v3 (recommended)
```bash
python src/show_v3.py --user <username> ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir nightly-run --threads 10
```

### show_v2 (legacy variant)
```bash
python src/show_v2.py --user <username> ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmds "show version,show ip interface brief" ^
    --output-dir nightly-run --combine
```

Both scripts prompt for `Password` and `Enable Password`, then spawn concurrent Netmiko sessions. Outputs appear under `outputs/<chosen-dir>`, alongside `connection_errors.txt` and `failed_ips.txt` if problems occurred.

## Testing
```bash
pytest
```
The suite validates helper utilities like file readers and output directory creation. Extend it when new functionality is added (e.g., parsing logic or custom logging).

## Tips
- Adjust `--threads` to match your environment capacity; avoid overwhelming network equipment.
- Keep `outputs/` clean by deleting folders from previous runs after collecting artifacts.
- Expand this document with troubleshooting guidance specific to your deployment.
