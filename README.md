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

## Getting Started
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt          # quick local experiments
# alternatively install the editable package (includes dev dependencies)
pip install -e .[dev]
```

## Usage
Examples assume you're at the project root.

```bash
# Run via console script (after pip install -e .)
show-cli --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir demo_outputs

# Run directly from source
python -m show_cli.main --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir demo_outputs

# Run with inline command list
python -m show_cli.main --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmds "show version,show ip interface brief" ^
    --output-dir demo_outputs --threads 5
```

Provide your own credentials when prompted. Outputs and logs land in `outputs/<chosen-dir>`; combine everything into one file with `--combine`. Fine-tune Netmiko behaviour from the CLI using `--log-level`, `--command-timeout`, `--delay-factor`, or `--session-timeout`.

### Using a Config File

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

Save it as `data/templates/config_template.ini`, then run:

```bash
show-cli --config data/templates/config_template.ini
```

CLI arguments always win over config defaults. Add extra keys—`command_timeout`, `delay_factor`, `session_timeout`, etc.—when you need slower devices to complete successfully. If the config lives under `data/`, just reference the filename:

```bash
show-cli --config config.ini   # automatically searches the project root and data/
```

## Data Management
- Put real/sensitive device lists in `data/raw/` (ignored by Git). Use the templates in `data/templates/` to track the required format.
- Place reusable examples in `data/inputs/` so contributors can reproduce behaviour.
- Large command or IP lists should live in `data/raw/` and stay out of version control.
- Use `data/templates/config_template.ini` as the baseline configuration example.

## Testing
```bash
python -m pytest
```
The suite currently covers helper utilities (file readers, path resolution, config parsing). 

## Documentation
More detailed walkthroughs live under `docs/usage.md`.

## License
Distributed under a custom non-commercial license. You may use, modify, and share the code for non-commercial purposes, but only MIFTA may grant commercial rights. See `LICENSE` for full terms.
