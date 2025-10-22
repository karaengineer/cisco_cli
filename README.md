# Show CLI Utility

Python-based CLI that automates Netmiko commands across multiple Cisco devices. It reads device and command lists under `data/`, executes them concurrently, and saves artefacts in `outputs/`.

## Features
- Multithreaded execution with per-device logging (`show_cli/main.py`).
- Configurable inputs: manual entry, text files, or command lists.
- Structured outputs with automatic error and failed-IP tracking.
- Sample data and raw data separation to help keep the repository light.
- Structured logging with adjustable verbosity (`--log-level`).
- Optional INI configuration file so you can store defaults once.

## Project Layout
```
./README.md
./CHANGELOG.md
./requirements.txt
./.github/workflows/
    ci.yml
./show_cli/
    __init__.py
    main.py
./data/
    inputs/          # tracked sample inputs for quick tests
    raw/             # large or sensitive datasets (ignored)
    templates/       # helper templates for user-specific data
./outputs/          # generated at runtime (ignored)
./tests/
    test_show_cli.py
./docs/
    usage.md
./LICENSE
```

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt   # lightweight install for quick trials
pip install -e .[dev]             # editable install with dev/test dependencies
```

## Usage
All commands below assume you run them from the project root and the virtual environment is active.

### Run with explicit arguments

```powershell
# Windows PowerShell (caret for line continuation)
show-cli --user admin `
    --ip-file data/inputs/ip_sample.txt `
    --cmd-file data/inputs/show_sample.txt `
    --output-dir demo_outputs
```

```bash
# macOS / Linux (backslash for line continuation)
show-cli --user admin \
  --ip-file data/inputs/ip_sample.txt \
  --cmd-file data/inputs/show_sample.txt \
  --output-dir demo_outputs
```

Prefer to run straight from the source module?

```powershell
python -m show_cli.main --user admin `
    --ip-file data/inputs/ip_sample.txt `
    --cmds "show version,show ip interface brief" `
    --output-dir demo_outputs --threads 5
```

During execution you will be prompted for `Password` and `Enable Password`. The tool writes one log file per device (unless `--combine` is set) and captures failures inside `outputs/<chosen-dir>/connection_errors.txt` and `failed_ips.txt`. Tune Netmiko behaviour on the fly with `--log-level`, `--command-timeout`, `--delay-factor`, and `--session-timeout`.

### Configuration file

```ini
[cli]
user = admin
# password = your-device-password        # optional; plaintext storage
# enable_password = your-enable-password  # optional; plaintext storage
ip_file = inputs/ip_sample.txt
cmd_file = inputs/show_sample.txt
threads = 8
combine = true
log_level = INFO
command_timeout = 300
delay_factor = 2.0
session_timeout = 30
```

Save it as `data/config.ini` (or any other relative path), then launch the CLI with:

```bash
show-cli --config config.ini
```

The loader searches the project root and `data/` directory automatically, so `--config config.ini` works for both `config.ini` and `data/config.ini`. Any CLI flag overrides the file value, allowing quick ad-hoc tweaks without editing the configuration. Extend the file with additional keys (`command_timeout`, `delay_factor`, `session_timeout`, etc.) whenever your devices need more relaxed timings. If you decide to store `password` or `enable_password` in the file, secure the file appropriately because the values are stored in plain text.

### Output folders

By default each execution writes to `outputs/<subdir>`:
- Per-device files (or a single `combined_output.txt` when `--combine` is used)
- `connection_errors.txt` containing the full exception text per failure
- `failed_ips.txt` capturing the IP list that needs attention

## Data Management
- Keep production or sensitive lists inside `data/raw/` (ignored by Git). The template files in `data/templates/` document the expected formats.
- Place reusable examples in `data/inputs/` so contributors can reproduce behaviour.
- Large command or IP lists should live in `data/raw/` and stay out of version control.
- Use `data/templates/config_template.ini` as the baseline configuration example.

## Testing
```bash
python -m pytest
```
The test suite currently exercises helper utilities (file readers, path resolution, configuration parsing). Add device-level mocks or integration scenarios as the CLI evolves.

## Documentation
More detailed walkthroughs live under `docs/usage.md`.

## License
Distributed under a custom non-commercial license. You may use, modify, and share the code for non-commercial purposes, but only MIFTA may grant commercial rights. See `LICENSE` for full terms.
